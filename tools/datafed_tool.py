from datafed.CommandLib import API
import json


class DataFedTool:

    def __init__(self, context="p/cnms"):
        self.api = API()
        self.api.setContext(context)

    def list_collection(self, collection_id: str):
        resp = self.api.collectionItemsList(collection_id)

        results = []
        for item in resp[0].item:
            results.append({
                "id": item.id,
                "title": item.title
            })

        return results

    def get_metadata(self, data_id: str):
        resp = self.api.dataView(data_id)
        record = resp[0].data[0]

        metadata = {}

        if record.metadata:
            try:
                metadata = json.loads(record.metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = record.metadata

        return {
            "id": record.id,
            "title": record.title,
            "metadata": metadata
        }

    def get_provenance(self, data_id: str):
        resp = self.api.dataView(data_id)
        record = resp[0].data[0]

        relationships = []

        for dep in record.deps:
            relationships.append({
                "id": dep.id,
                "alias": dep.alias,
                "type": str(dep.type),
                "direction": str(dep.dir),
            })

        return {
            "id": record.id,
            "title": record.title,
            "relationships": relationships,
        }
        
    def inspect_record(self, data_id: str):
        """
        Return all information DataFed exposes for a record
        without downloading the underlying scientific file.
        """
        resp = self.api.dataView(data_id)
        record = resp[0].data[0]
        result = {}
        for field, value in record.ListFields():
            name = field.name
            if name == "metadata" and value:
                try:
                    result[name] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[name] = value
            elif field.is_repeated:
                result[name] = [str(v) for v in value]
            else:
                result[name] = str(value)
        return result
    
    def search_collections(self, query: str, root_id="c/p_cnms_root"):
        """
        Recursively search collections/subcollections.
        Matching is case-insensitive and allows the query
        to be only part of the collection title.
        """
        query = query.lower().strip()
        matches = []
        def walk_collection(collection_id):
            resp = self.api.collectionItemsList(collection_id)
            for item in resp[0].item:
                item_id = item.id
                title = item.title or ""
                # Collection IDs begin with c/
                if item_id.startswith("c/"):
                    # Partial, case-insensitive match
                    if query in title.lower():
                        matches.append({
                            "id": item_id,
                            "title": title
                        })
                    # Search inside this subcollection
                    walk_collection(item_id)
        walk_collection(root_id)
        return matches
          
    def search_records(self,query: str,collection_id: str | None = None,count: int = 20):
        """
        Search DataFed data records by title/description text.
        If collection_id is provided, restrict the search
        to that collection.
        """
        kwargs = {
            "text": query,
            "count": count,
        }
        if collection_id:
            kwargs["coll"] = [collection_id]
        resp = self.api.queryDirect(**kwargs)
        results = []
    
        for item in resp[0].item:
            results.append({
                "id": item.id,
                "title": item.title,
            })
        return results
        
        

    def plot_distribution(self,file_path: str,dataset_path: str,bins: int = 50,output_dir: str = "/tmp/brave_agent"):
        """
        Plot the distribution of values from any numerical dataset.
    
        The function makes no assumptions about instrument type,
        scientific modality, or meaning of the values.
        """
    
        # Read numerical data using the existing method
        data = self.get_data(file_path=file_path,dataset_path=dataset_path)
    
        # Convert N-D array into a 1-D collection of values
        values = np.asarray(data).ravel()
        # Remove NaN and infinite values
        values = values[np.isfinite(values)]
    
        if values.size == 0:
            raise ValueError(f"Dataset '{dataset_path}' contains no finite numerical values.")
    
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
        safe_name = dataset_path.strip("/").replace("/", "_")
        output_path = output_dir / f"{safe_name}_distribution.png"
    
        # Generate histogram
        plt.figure(figsize=(7, 5))
        plt.hist(values,bins=bins)
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.title(f"Distribution — {dataset_path}")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150,bbox_inches="tight")
        plt.close()
    
        # Also return basic statistics.
        # These will be useful to the LLM when answering scientific questions.
        return {
            "dataset_path": dataset_path,
            "shape": list(data.shape),
            "dtype": str(data.dtype),
            "n_values": int(values.size),
            "minimum": float(np.min(values)),
            "maximum": float(np.max(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "bins": bins,
            "plot_path": str(output_path),
        }