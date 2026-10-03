from pathlib import Path

import h5py
import numpy as np
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


class ScientificTool:

    def inspect_h5_datasets(self, file_path: str):
        """
        Discover numerical datasets inside an HDF5/H5/NXS file.

        No assumptions are made about instrument type,
        channel names, or HDF5 layout.
        """

        datasets = []
        with h5py.File(file_path, "r") as h5:
            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    datasets.append({
                        "path": name,
                        "shape": list(obj.shape),
                        "dtype": str(obj.dtype),
                        "ndim": obj.ndim,
                    })
            h5.visititems(visitor)
        return datasets


    def get_data(self, file_path: str, dataset_path: str):
        """
        Read a numerical dataset from a scientific HDF5 file.
        """
        with h5py.File(file_path, "r") as h5:
            if dataset_path not in h5:
                raise ValueError(
                    f"Dataset '{dataset_path}' not found."
                )
            data = np.asarray(h5[dataset_path])
        return data


    def visualize_data(self, file_path: str,dataset_path: str,output_dir: str = "/tmp/brave_agent"):
        """
        Generate a visualization based on the dimensionality
        of the selected numerical dataset.
        """
        data = self.get_data(file_path=file_path,dataset_path=dataset_path)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = dataset_path.strip("/").replace("/", "_")
        output_path = output_dir / f"{safe_name}.png"
        plt.figure(figsize=(7, 5))
        if data.ndim == 1:
            plt.plot(data)
            plt.xlabel("Index")
            plt.ylabel("Value")
        elif data.ndim == 2:
            image = plt.imshow(data,origin="lower", aspect="auto")
            plt.colorbar(image, label="Value")
        elif data.ndim == 3:

            # Generic default representation:
            # display the central slice.
            slice_index = data.shape[0] // 2
            image = plt.imshow(
                data[slice_index],
                origin="lower",
                aspect="auto"
            )
            plt.colorbar(image, label="Value")
            plt.title(f"{dataset_path} — slice {slice_index}")
        else:
            plt.close()
            raise ValueError(
                f"Cannot automatically visualize "
                f"{data.ndim}D data."
            )
        if data.ndim != 3:
            plt.title(dataset_path)
        plt.tight_layout()
        plt.savefig(output_path,dpi=150,bbox_inches="tight")
        plt.close()
        return {
            "dataset_path": dataset_path,
            "shape": list(data.shape),
            "dtype": str(data.dtype),
            "ndim": data.ndim,
            "plot_path": str(output_path),
        }