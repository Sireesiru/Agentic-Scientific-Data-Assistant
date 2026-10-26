from pathlib import Path
import h5py
import numpy as np
import matplotlib
from scipy import stats
matplotlib.use("Agg")

import matplotlib.pyplot as plt


class ScientificTool:

    # ============================================================
    # INSPECT HDF5
    # ============================================================

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

    # ============================================================
    # READ DATA
    # ============================================================

    def get_data(self, file_path: str, dataset_path: str):
        """
        Read a numerical dataset from a scientific HDF5 file.
        """

        with h5py.File(file_path, "r") as h5:

            if dataset_path not in h5:
                raise ValueError(
                    f"Dataset '{dataset_path}' not found."
                )

            data = np.asarray(
                h5[dataset_path]
            )

        return data

    # ============================================================
    # VISUALIZE DATA
    # ============================================================

    def visualize_data(
        self,
        file_path: str,
        dataset_path: str,
        output_dir: str = "/tmp/brave_agent",
    ):
        """
        Generate a visualization based on the dimensionality
        of the selected numerical dataset.
        """

        data = self.get_data(
            file_path=file_path,
            dataset_path=dataset_path,
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_name = (
            dataset_path
            .strip("/")
            .replace("/", "_")
        )

        output_path = (
            output_dir / f"{safe_name}.png"
        )

        plt.figure(figsize=(7, 5))

        # --------------------------------------------------------
        # 1-D data
        # --------------------------------------------------------

        if data.ndim == 1:

            plt.plot(data)

            plt.xlabel("Index")
            plt.ylabel("Value")

        # --------------------------------------------------------
        # 2-D data
        # --------------------------------------------------------

        elif data.ndim == 2:

            image = plt.imshow(
                data,
                origin="lower",
                aspect="auto",
            )

            plt.colorbar(
                image,
                label="Value",
            )

        # --------------------------------------------------------
        # 3-D data
        # --------------------------------------------------------

        elif data.ndim == 3:

            # Generic representation:
            # display the central slice.

            slice_index = (
                data.shape[0] // 2
            )

            image = plt.imshow(
                data[slice_index],
                origin="lower",
                aspect="auto",
            )

            plt.colorbar(
                image,
                label="Value",
            )

            plt.title(
                f"{dataset_path} — "
                f"slice {slice_index}"
            )

        else:

            plt.close()

            raise ValueError(
                f"Cannot automatically visualize "
                f"{data.ndim}D data."
            )

        if data.ndim != 3:
            plt.title(dataset_path)

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        return {
            "dataset_path": dataset_path,
            "shape": list(data.shape),
            "dtype": str(data.dtype),
            "ndim": data.ndim,
            "plot_path": str(output_path),
        }

    # ============================================================
    # VALUE DISTRIBUTION
    # ============================================================

    def plot_distribution(
        self,
        file_path: str,
        dataset_path: str,
        bins: int = 50,
        output_dir: str = "/tmp/brave_agent",
    ):
        """
        Plot the value distribution of a numerical HDF5 dataset
        and return descriptive statistics.

        No assumptions are made about instrument type or
        scientific meaning of the values.
        """

        data = self.get_data(
            file_path=file_path,
            dataset_path=dataset_path,
        )

        # Flatten N-dimensional numerical data.
        values = np.asarray(data).ravel()

        # Keep only finite values.
        values = values[
            np.isfinite(values)
        ]

        if values.size == 0:
            raise ValueError(
                f"Dataset '{dataset_path}' "
                f"contains no finite numerical values."
            )

        output_dir = Path(output_dir)

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_name = (
            dataset_path
            .strip("/")
            .replace("/", "_")
        )

        output_path = (
            output_dir
            / f"{safe_name}_distribution.png"
        )

        # --------------------------------------------------------
        # Histogram
        # --------------------------------------------------------

        plt.figure(figsize=(7, 5))

        plt.hist(
            values,
            bins=bins,
        )

        plt.xlabel("Value")
        plt.ylabel("Frequency")

        plt.title(
            f"Distribution — {dataset_path}"
        )

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        # --------------------------------------------------------
        # Descriptive statistics
        # --------------------------------------------------------

        return {
            "dataset_path": dataset_path,
            "shape": list(data.shape),
            "dtype": str(data.dtype),
            "n_values": int(values.size),
            "minimum": float(
                np.min(values)
            ),
            "maximum": float(
                np.max(values)
            ),
            "mean": float(
                np.mean(values)
            ),
            "median": float(
                np.median(values)
            ),
            "std": float(
                np.std(values)
            ),
            "bins": bins,
            "plot_path": str(output_path),
        }
        
    def compare_datasets(
        self,
        file_path_a: str,
        dataset_path_a: str,
        file_path_b: str,
        dataset_path_b: str,
        output_dir: str = "/tmp/brave_agent",
    ):
        """
        Compare two numerical HDF5 datasets.

        The datasets may come from:
        - the same HDF5 file, or
        - two different HDF5 files.

        Returns descriptive statistics for both datasets.

        If the arrays have the same shape, also returns pixel-wise:
        - mean difference (A - B)
        - mean absolute difference
        - RMSE
        - Pearson correlation

        For same-shape 2D arrays, also generates:
        - signed difference map
        - absolute difference map
        """

        file_path_a = str(file_path_a)
        file_path_b = str(file_path_b)

        data_a = np.asarray(
            self.get_data(file_path_a, dataset_path_a),
            dtype=np.float64,
        )

        data_b = np.asarray(
            self.get_data(file_path_b, dataset_path_b),
            dtype=np.float64,
        )

        finite_a = data_a[np.isfinite(data_a)]
        finite_b = data_b[np.isfinite(data_b)]

        if finite_a.size == 0:
            raise ValueError(
                f"Dataset A contains no finite numerical values: "
                f"{dataset_path_a}"
            )

        if finite_b.size == 0:
            raise ValueError(
                f"Dataset B contains no finite numerical values: "
                f"{dataset_path_b}"
            )

        result = {
            "file_path_a": file_path_a,
            "dataset_path_a": dataset_path_a,
            "file_path_b": file_path_b,
            "dataset_path_b": dataset_path_b,

            "shape_a": list(data_a.shape),
            "shape_b": list(data_b.shape),

            "n_a": int(finite_a.size),
            "n_b": int(finite_b.size),

            "min_a": float(np.min(finite_a)),
            "max_a": float(np.max(finite_a)),
            "mean_a": float(np.mean(finite_a)),
            "median_a": float(np.median(finite_a)),
            "std_a": float(np.std(finite_a)),

            "min_b": float(np.min(finite_b)),
            "max_b": float(np.max(finite_b)),
            "mean_b": float(np.mean(finite_b)),
            "median_b": float(np.median(finite_b)),
            "std_b": float(np.std(finite_b)),

            "same_shape": bool(data_a.shape == data_b.shape),
            "pixelwise_comparison": False,

            "mean_difference": None,
            "mean_absolute_difference": None,
            "rmse": None,
            "pearson_correlation": None,

            "difference_plot_path": None,
            "absolute_difference_plot_path": None,
        }

        # Pixel-wise comparison only makes scientific/mathematical sense
        # here when the arrays have identical shapes.
        if data_a.shape != data_b.shape:
            return result

        paired_mask = np.isfinite(data_a) & np.isfinite(data_b)

        if not np.any(paired_mask):
            return result

        paired_a = data_a[paired_mask]
        paired_b = data_b[paired_mask]

        differences = paired_a - paired_b

        result["pixelwise_comparison"] = True
        result["paired_n"] = int(differences.size)

        result["mean_difference"] = float(np.mean(differences))
        result["mean_absolute_difference"] = float(
            np.mean(np.abs(differences))
        )
        result["rmse"] = float(
            np.sqrt(np.mean(differences ** 2))
        )

        std_a = np.std(paired_a)
        std_b = np.std(paired_b)

        if std_a > 0 and std_b > 0:
            result["pearson_correlation"] = float(
                np.corrcoef(paired_a, paired_b)[0, 1]
            )

        # Generate spatial maps only for 2D arrays.
        if data_a.ndim == 2:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            difference_map = np.full(
                data_a.shape,
                np.nan,
                dtype=np.float64,
            )

            absolute_difference_map = np.full(
                data_a.shape,
                np.nan,
                dtype=np.float64,
            )

            difference_map[paired_mask] = (
                data_a[paired_mask] - data_b[paired_mask]
            )

            absolute_difference_map[paired_mask] = np.abs(
                data_a[paired_mask] - data_b[paired_mask]
            )

            def safe_name(value):
                return (
                    str(value)
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace(" ", "_")
                    .replace(":", "_")
                )

            name_a = safe_name(dataset_path_a)
            name_b = safe_name(dataset_path_b)

            difference_plot = (
                output_path
                / f"compare_{name_a}_VS_{name_b}_difference.png"
            )

            absolute_difference_plot = (
                output_path
                / f"compare_{name_a}_VS_{name_b}_absolute_difference.png"
            )

            plt.figure(figsize=(7, 6))
            image = plt.imshow(difference_map)
            plt.colorbar(image, label="A - B")
            plt.title("Signed difference: A - B")
            plt.xlabel("X pixel")
            plt.ylabel("Y pixel")
            plt.tight_layout()
            plt.savefig(
                difference_plot,
                dpi=150,
                bbox_inches="tight",
            )
            plt.close()

            plt.figure(figsize=(7, 6))
            image = plt.imshow(absolute_difference_map)
            plt.colorbar(image, label="|A - B|")
            plt.title("Absolute difference: |A - B|")
            plt.xlabel("X pixel")
            plt.ylabel("Y pixel")
            plt.tight_layout()
            plt.savefig(
                absolute_difference_plot,
                dpi=150,
                bbox_inches="tight",
            )
            plt.close()

            result["difference_plot_path"] = str(
                difference_plot
            )

            result["absolute_difference_plot_path"] = str(
                absolute_difference_plot
            )

        return result
        
    def compare_distributions(
        self,
        file_path_a: str,
        dataset_path_a: str,
        file_path_b: str,
        dataset_path_b: str,
        output_dir: str = "/tmp/brave_agent",
        bins: int = 100,
    ):
        """
        Compare the numerical value distributions of two HDF5 datasets.

        This comparison does NOT require:
        - equal array shapes,
        - pixel alignment,
        - spatial registration.

        It is therefore useful for comparing independent experimental
        images or measurements when pixel-wise correspondence is not
        scientifically meaningful.

        Returns:
        - descriptive statistics for A and B
        - difference in means
        - difference in medians
        - two-sample Kolmogorov-Smirnov statistic
        - KS p-value
        - overlaid normalized histogram
        """

        file_path_a = str(file_path_a)
        file_path_b = str(file_path_b)

        data_a = np.asarray(
            self.get_data(file_path_a, dataset_path_a),
            dtype=np.float64,
        )

        data_b = np.asarray(
            self.get_data(file_path_b, dataset_path_b),
            dtype=np.float64,
        )

        values_a = data_a[np.isfinite(data_a)]
        values_b = data_b[np.isfinite(data_b)]

        if values_a.size == 0:
            raise ValueError(
                f"Dataset A contains no finite numerical values: "
                f"{dataset_path_a}"
            )

        if values_b.size == 0:
            raise ValueError(
                f"Dataset B contains no finite numerical values: "
                f"{dataset_path_b}"
            )

        mean_a = float(np.mean(values_a))
        mean_b = float(np.mean(values_b))

        median_a = float(np.median(values_a))
        median_b = float(np.median(values_b))

        std_a = float(np.std(values_a))
        std_b = float(np.std(values_b))

        ks_result = stats.ks_2samp(
            values_a,
            values_b,
            alternative="two-sided",
            method="auto",
        )

        result = {
            "file_path_a": file_path_a,
            "dataset_path_a": dataset_path_a,
            "file_path_b": file_path_b,
            "dataset_path_b": dataset_path_b,

            "shape_a": list(data_a.shape),
            "shape_b": list(data_b.shape),

            "n_a": int(values_a.size),
            "n_b": int(values_b.size),

            "min_a": float(np.min(values_a)),
            "max_a": float(np.max(values_a)),
            "mean_a": mean_a,
            "median_a": median_a,
            "std_a": std_a,

            "min_b": float(np.min(values_b)),
            "max_b": float(np.max(values_b)),
            "mean_b": mean_b,
            "median_b": median_b,
            "std_b": std_b,

            "mean_difference": float(mean_a - mean_b),
            "median_difference": float(median_a - median_b),

            "ks_statistic": float(ks_result.statistic),
            "ks_pvalue": float(ks_result.pvalue),

            "distribution_plot_path": None,
        }

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        def safe_name(value):
            return (
                str(value)
                .replace("/", "_")
                .replace("\\", "_")
                .replace(" ", "_")
                .replace(":", "_")
            )

        name_a = safe_name(dataset_path_a)
        name_b = safe_name(dataset_path_b)

        distribution_plot = (
            output_path
            / f"distribution_{name_a}_VS_{name_b}.png"
        )

        # Use a shared range so both histograms are directly comparable.
        combined_min = min(
            float(np.min(values_a)),
            float(np.min(values_b)),
        )

        combined_max = max(
            float(np.max(values_a)),
            float(np.max(values_b)),
        )

        if combined_min == combined_max:
            combined_min -= 0.5
            combined_max += 0.5

        plt.figure(figsize=(8, 6))

        plt.hist(
            values_a,
            bins=bins,
            range=(combined_min, combined_max),
            density=True,
            alpha=0.5,
            label="Dataset A",
        )

        plt.hist(
            values_b,
            bins=bins,
            range=(combined_min, combined_max),
            density=True,
            alpha=0.5,
            label="Dataset B",
        )

        plt.xlabel("Value")
        plt.ylabel("Probability density")
        plt.title("Dataset value distributions")
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            distribution_plot,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()

        result["distribution_plot_path"] = str(
            distribution_plot
        )

        return result        
        
        
        # ---------------------------------------------------------
        # Load datasets
        # ---------------------------------------------------------
    
        a = np.asarray(
            self.get_data(file_path, dataset_path_a),
            dtype=np.float64,
        )
    
        b = np.asarray(
            self.get_data(file_path, dataset_path_b),
            dtype=np.float64,
        )
    
        # ---------------------------------------------------------
        # Basic validation
        # ---------------------------------------------------------
    
        if a.size == 0 or b.size == 0:
            raise ValueError("One or both datasets are empty.")
    
        finite_a = np.isfinite(a)
        finite_b = np.isfinite(b)
    
        values_a = a[finite_a]
        values_b = b[finite_b]
    
        if values_a.size == 0 or values_b.size == 0:
            raise ValueError(
                "One or both datasets contain no finite numerical values."
            )
    
        # ---------------------------------------------------------
        # Independent descriptive statistics
        # ---------------------------------------------------------
    
        result = {
            "dataset_a": dataset_path_a,
            "dataset_b": dataset_path_b,
    
            "shape_a": list(a.shape),
            "shape_b": list(b.shape),
    
            "n_values_a": int(values_a.size),
            "n_values_b": int(values_b.size),
    
            "minimum_a": float(np.min(values_a)),
            "maximum_a": float(np.max(values_a)),
            "mean_a": float(np.mean(values_a)),
            "median_a": float(np.median(values_a)),
            "std_a": float(np.std(values_a)),
    
            "minimum_b": float(np.min(values_b)),
            "maximum_b": float(np.max(values_b)),
            "mean_b": float(np.mean(values_b)),
            "median_b": float(np.median(values_b)),
            "std_b": float(np.std(values_b)),
    
            "same_shape": bool(a.shape == b.shape),
        }
    
        # ---------------------------------------------------------
        # Pixel-wise comparison requires matching shapes
        # ---------------------------------------------------------
    
        if a.shape != b.shape:
            result.update(
                {
                    "pixelwise_comparison": False,
                    "reason": (
                        "Dataset shapes differ. Descriptive statistics "
                        "were calculated, but pixel-wise comparison was "
                        "not performed."
                    ),
                }
            )
    
            return result
    
        # ---------------------------------------------------------
        # Use only pixels finite in BOTH arrays
        # ---------------------------------------------------------
    
        valid = np.isfinite(a) & np.isfinite(b)
    
        paired_a = a[valid]
        paired_b = b[valid]
    
        if paired_a.size == 0:
            raise ValueError(
                "The datasets contain no mutually finite pixels."
            )
    
        difference_values = paired_a - paired_b
    
        # ---------------------------------------------------------
        # Comparison metrics
        # ---------------------------------------------------------
    
        mean_difference = np.mean(difference_values)
        mae = np.mean(np.abs(difference_values))
        rmse = np.sqrt(np.mean(difference_values ** 2))
    
        # Pearson requires variation in both arrays
        if np.std(paired_a) > 0 and np.std(paired_b) > 0:
            pearson = np.corrcoef(
                paired_a,
                paired_b,
            )[0, 1]
    
            pearson_value = float(pearson)
        else:
            pearson_value = None
    
        # ---------------------------------------------------------
        # Full spatial difference arrays
        # ---------------------------------------------------------
    
        difference_map = np.full(
            a.shape,
            np.nan,
            dtype=np.float64,
        )
    
        difference_map[valid] = a[valid] - b[valid]
    
        absolute_difference_map = np.abs(difference_map)
    
        # ---------------------------------------------------------
        # Output directory
        # ---------------------------------------------------------
    
        output_path = Path(output_dir)
        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )
    
        # Generate safe filename
        safe_a = (
            dataset_path_a
            .replace("/", "_")
            .replace("\\", "_")
        )
    
        safe_b = (
            dataset_path_b
            .replace("/", "_")
            .replace("\\", "_")
        )
    
        # Keep filename from becoming excessively long
        safe_a = safe_a[-100:]
        safe_b = safe_b[-100:]
    
        difference_plot_path = (
            output_path
            / f"compare_{safe_a}_VS_{safe_b}_difference.png"
        )
    
        absolute_difference_plot_path = (
            output_path
            / f"compare_{safe_a}_VS_{safe_b}_absolute_difference.png"
        )
    
        # ---------------------------------------------------------
        # Signed difference map
        # ---------------------------------------------------------
    
        if difference_map.ndim == 2:
    
            fig, ax = plt.subplots(figsize=(7, 6))
    
            image = ax.imshow(
                difference_map,
                origin="lower",
                aspect="auto",
            )
    
            ax.set_title("Difference Map: Dataset A - Dataset B")
            ax.set_xlabel("X pixel")
            ax.set_ylabel("Y pixel")
    
            fig.colorbar(
                image,
                ax=ax,
                label="Difference",
            )
    
            fig.tight_layout()
    
            fig.savefig(
                difference_plot_path,
                dpi=150,
                bbox_inches="tight",
            )
    
            plt.close(fig)
    
            # -----------------------------------------------------
            # Absolute difference map
            # -----------------------------------------------------
    
            fig, ax = plt.subplots(figsize=(7, 6))
    
            image = ax.imshow(
                absolute_difference_map,
                origin="lower",
                aspect="auto",
            )
    
            ax.set_title("Absolute Difference Map")
            ax.set_xlabel("X pixel")
            ax.set_ylabel("Y pixel")
    
            fig.colorbar(
                image,
                ax=ax,
                label="Absolute difference",
            )
    
            fig.tight_layout()
    
            fig.savefig(
                absolute_difference_plot_path,
                dpi=150,
                bbox_inches="tight",
            )
    
            plt.close(fig)
    
            difference_plot = str(difference_plot_path)
            absolute_difference_plot = str(
                absolute_difference_plot_path
            )
    
        else:
            # Numerical comparison still works for non-2D arrays,
            # but image maps are only generated for 2D datasets.
            difference_plot = None
            absolute_difference_plot = None
    
        # ---------------------------------------------------------
        # Final result
        # ---------------------------------------------------------
    
        result.update(
            {
                "pixelwise_comparison": True,
                "n_paired_values": int(paired_a.size),
                "mean_difference": float(mean_difference),
                "mean_absolute_difference": float(mae),
                "rmse": float(rmse),
                "pearson_correlation": pearson_value,
                "difference_plot_path": difference_plot,
                "absolute_difference_plot_path": absolute_difference_plot,
            }
        )
        return result
    
    
    
    
    
    
    
    
    
    
    
    