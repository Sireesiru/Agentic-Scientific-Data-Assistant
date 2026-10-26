from datafed.CommandLib import API
import json
from pathlib import Path


class DataFedTool:

    def __init__(self, context="p/cnms"):
        self.api = API()
        self.api.setContext(context)

    # ============================================================
    # COLLECTION LISTING
    # ============================================================

    def list_collection(self, collection_id: str):
        resp = self.api.collectionItemsList(collection_id)

        results = []

        for item in resp[0].item:
            results.append({
                "id": item.id,
                "title": item.title
            })

        return results

    # ============================================================
    # METADATA
    # ============================================================

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

    # ============================================================
    # PROVENANCE
    # ============================================================

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

    # ============================================================
    # FULL DATAFED RECORD INSPECTION
    # ============================================================

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

    # ============================================================
    # RESOLVE DATAFED RECORD TO LOCAL FILE
    # ============================================================

    def resolve_record_file(self, data_id: str):
        """
        Resolve a DataFed record to a locally accessible file.

        Strategy:

        1. Inspect the record's DataFed source location.

        2. If the source belongs to the Globus endpoint mounted on
           Microflows, translate the Globus-visible path:

               /home/gridftp/data/...

           to the Microflows local path:

               /home/cloud/Globus-Personal-Docker/data/...

        3. If the original file still exists locally, return it
           directly.

        4. If it no longer exists locally, fall back to DataFed
           dataGet() retrieval.

        This keeps the resolver independent of AFM, cryo-EM,
        RHEED, or any particular subdirectory.
        """

        config_path = (
            "/home/cloud/cnms-qr-sample-tracking-main/config.json"
        )

        with open(config_path, "r") as f:
            config = json.load(f)

        globus_collection = (
            config["globus"]["src_collection"].strip()
        )

        globus_root = config["globus"].get(
            "endpoint_path",
            "/home/gridftp/data/"
        )

        local_root = Path(
            config["pipeline"]["watch_directory"]
        )

        # Make sure roots behave consistently.
        if not globus_root.endswith("/"):
            globus_root += "/"

        # --------------------------------------------------------
        # Read full DataFed record
        # --------------------------------------------------------

        resp = self.api.dataView(data_id)
        record = resp[0].data[0]

        source = getattr(record, "source", None)

        # --------------------------------------------------------
        # Attempt local source resolution
        # --------------------------------------------------------

        if source:
            source = str(source)

            # Example source:
            #
            # 653ec3d7-.../home/gridftp/data/AFM/old_files/file.h5.nxs

            if source.startswith(globus_collection):

                endpoint_path = source[
                    len(globus_collection):
                ]

                if endpoint_path.startswith(globus_root):

                    relative_path = endpoint_path[
                        len(globus_root):
                    ].lstrip("/")

                    local_path = local_root / relative_path

                    if local_path.is_file():

                        print(
                            f"Using existing local source for "
                            f"{data_id}: {local_path}"
                        )

                        return {
                            "data_id": data_id,
                            "local_path": str(local_path),
                            "filename": local_path.name,
                            "size_bytes": local_path.stat().st_size,
                            "access_method": "existing_local_source",
                            "temporary": False,
                        }

        # --------------------------------------------------------
        # Local source is unavailable.
        # Fall back to DataFed retrieval.
        # --------------------------------------------------------

        print(
            f"Local source unavailable for {data_id}. "
            f"Attempting DataFed retrieval."
        )

        result = self.download_record(data_id)

        result["access_method"] = "datafed_download"
        result["temporary"] = True

        return result

    # ============================================================
    # DATAFED DOWNLOAD
    # ============================================================

    def download_record(
        self,
        data_id: str,
        output_dir: str = (
            "/home/cloud/Globus-Personal-Docker/"
            "data/agent_downloads"
        ),
    ):
        """
        Retrieve a DataFed record through the configured Globus
        collection so that local scientific tools can inspect it.

        NOTE:
        The DataFed/Globus fallback is retained here. We are still
        investigating why dataGet() currently returns without a
        file appearing in the expected local destination.
        """

        config_path = (
            "/home/cloud/cnms-qr-sample-tracking-main/config.json"
        )

        with open(config_path, "r") as f:
            config = json.load(f)

        globus_collection = (
            config["globus"]["src_collection"].strip()
        )

        globus_root = config["globus"].get(
            "endpoint_path",
            "/home/gridftp/data/"
        )

        if not globus_root.endswith("/"):
            globus_root += "/"

        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Microflows local staging root
        staging_root = Path(
            config["pipeline"]["watch_directory"]
        )

        # Ensure requested download directory is inside staging.
        try:
            relative_dir = output_dir.relative_to(
                staging_root
            )
        except ValueError:
            raise ValueError(
                f"Download directory {output_dir} must be "
                f"inside staging root {staging_root}"
            )

        # Translate local destination into the path visible
        # through the Globus endpoint.
        globus_destination = (
            f"{globus_collection}"
            f"{globus_root}"
            f"{relative_dir.as_posix()}/"
        )

        print(
            f"Retrieving {data_id} from DataFed "
            f"to {globus_destination}"
        )

        self.api.dataGet(
            data_id,
            globus_destination,
            orig_fname=False,
            wait=True,
            timeout_sec=300,
        )

        # --------------------------------------------------------
        # Find transferred file
        # --------------------------------------------------------

        files = [
            p
            for p in output_dir.rglob("*")
            if p.is_file()
        ]

        if not files:
            raise FileNotFoundError(
                f"DataFed transfer completed but no file "
                f"was found in {output_dir}"
            )

        # When orig_fname=False, DataFed may name the
        # downloaded object using its record identifier.
        record_number = data_id.split("/")[-1]

        matching = [
            p
            for p in files
            if record_number in p.name
        ]

        if matching:
            selected = max(
                matching,
                key=lambda p: p.stat().st_mtime,
            )
        else:
            selected = max(
                files,
                key=lambda p: p.stat().st_mtime,
            )

        return {
            "data_id": data_id,
            "local_path": str(selected),
            "filename": selected.name,
            "size_bytes": selected.stat().st_size,
        }

    # ============================================================
    # COLLECTION SEARCH
    # ============================================================

    def search_collections(
        self,
        query: str,
        root_id="c/p_cnms_root",
    ):
        """
        Recursively search collections/subcollections.

        Matching is case-insensitive and allows the query
        to be only part of the collection title.
        """

        query = query.lower().strip()

        matches = []

        def walk_collection(collection_id):

            resp = self.api.collectionItemsList(
                collection_id
            )

            for item in resp[0].item:

                item_id = item.id
                title = item.title or ""

                # Collection IDs begin with c/
                if item_id.startswith("c/"):

                    if query in title.lower():
                        matches.append({
                            "id": item_id,
                            "title": title
                        })

                    # Recursively search subcollections
                    walk_collection(item_id)

        walk_collection(root_id)

        return matches

    # ============================================================
    # RECORD SEARCH
    # ============================================================

    def search_records(
        self,
        query: str,
        collection_id: str | None = None,
        count: int = 20,
    ):
        """
        Search DataFed records by title/description text.

        If collection_id is supplied, restrict the search
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