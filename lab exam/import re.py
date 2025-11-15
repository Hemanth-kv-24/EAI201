import re
import json
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd


class AlphaIntegrator:
    def __init__(self,
                 search_dirs=None,
                 aux_json=Path("/mnt/data/auxiliary_metadata.json")):
        # directories to search for zoo/class files
        if search_dirs is None:
            search_dirs = [Path("/mnt/data"), Path("."), Path("/content"), Path.cwd()]
        # keep unique Path objects in order
        self.search_dirs = []
        for d in search_dirs:
            p = Path(d)
            if p not in self.search_dirs:
                self.search_dirs.append(p)
        self.aux_json = Path(aux_json)
        self.merged_data: Optional[pd.DataFrame] = None

    # File discovery & loaders
    def _find_file(self, name_patterns: Tuple[str, ...]) -> Optional[Path]:
        """Search search_dirs for a filename that matches any of the regex patterns.
        Returns first match (Path) or None."""
        for base in self.search_dirs:
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file():
                    for pat in name_patterns:
                        if re.search(pat, p.name, flags=re.IGNORECASE):
                            return p
        return None

    def _load_table_preferring_csv(self, stems: Tuple[str, ...]) -> Optional[Path]:
        """Find file by stems (like 'zoo', 'animal_zoo') and prefer CSV over XLSX.
        Returns the selected Path or None."""
        # Candidate regexes: look for exact stem with ext or stem anywhere
        csv_patterns = [rf"\b{re.escape(s)}\b.*\.csv$" for s in stems] + [rf"{re.escape(s)}.*\.csv$" for s in stems]
        xlsx_patterns = [rf"\b{re.escape(s)}\b.*\.(xlsx|xls)$" for s in stems] + [rf"{re.escape(s)}.*\.(xlsx|xls)$" for s in stems]

        # Try CSVs first
        for pat in csv_patterns:
            f = self._find_file((pat,))
            if f:
                return f

        # If no CSV, try xlsx/xls
        for pat in xlsx_patterns:
            f = self._find_file((pat,))
            if f:
                return f

        # not found
        return None

    def _read_any_table(self, path: Path) -> Optional[pd.DataFrame]:
        """Read CSV or Excel robustly. Returns DataFrame or None (and prints a message)."""
        if path is None:
            return None

        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                return pd.read_csv(path)
            if suffix in (".xlsx", ".xls"):
                try:
                    return pd.read_excel(path)
                except Exception as ex:
                    # Attempt a fallback: look for a CSV with same stem in same folder
                    alt_csv = path.with_suffix(".csv")
                    if alt_csv.exists():
                        try:
                            return pd.read_csv(alt_csv)
                        except Exception:
                            print(f"[ERROR] Found Excel {path.name} but failed to read it and fallback CSV {alt_csv.name} also failed.")
                            return None
                    # If no CSV fallback, print actionable message and return None (no exception)
                    print(f"[ERROR] Cannot read Excel file {path}. It may require an engine (openpyxl).")
                    print("Action: either convert that .xlsx to .csv or install openpyxl in your environment.")
                    return None
            # unknown suffix: try CSV read then excel read
            try:
                return pd.read_csv(path)
            except Exception:
                return pd.read_excel(path)
        except FileNotFoundError:
            return None
        except Exception as exc:
            print(f"[ERROR] Failed to read {path}: {exc}")
            return None
    # Auxiliary normalization
    @staticmethod
    def _normalize_aux_record(rec: dict) -> dict:
        low = {k.lower(): v for k, v in rec.items()}
        out = {}

        # animal name
        name = low.get("animal_name") or low.get("animal") or low.get("name")
        out["animal_name"] = name.strip().lower() if isinstance(name, str) else None

        # habitat variants -> habitat
        habitat = low.get("habitat") or low.get("habitats") or low.get("habitat_type")
        if isinstance(habitat, str):
            h = habitat.strip().lower()
            if "fresh" in h and "water" in h:
                h = "freshwater"
            out["habitat"] = " ".join(h.split())
        else:
            out["habitat"] = None

        # diet variants -> diet (fix common typos)
        diet = low.get("diet") or low.get("diet_type")
        if isinstance(diet, str):
            d = diet.strip().lower()
            if d.startswith("omnivor"):
                d = "omnivore"
            out["diet"] = d
        else:
            out["diet"] = None

        # conservation_status variants
        cons = low.get("conservation_status") or low.get("conservation") or low.get("status")
        if isinstance(cons, str):
            c = cons.strip().lower()
            if c == "least":
                c = "least concern"
            out["conservation_status"] = c
        else:
            out["conservation_status"] = None

        return out
   # Main integration method
    def alpha_load_and_integrate(self) -> Optional[pd.DataFrame]:
        """Load zoo, class and auxiliary, normalize names & JSON, merge, drop missing aux rows.
        Returns merged DataFrame or None (with printed guidance)."""
        # Find zoo file (prefer csv)
        zoo_file = self._load_table_preferring_csv(("zoo",))
        class_file = self._load_table_preferring_csv(("class", "Class"))

        if zoo_file is None:
            print("[ERROR] Zoo file not found. Looked for files with 'zoo' in their names under search dirs.")
            print("Please upload/put zoo.csv or zoo.xlsx into one of these folders:", self.search_dirs)
            return None
        if class_file is None:
            print("[ERROR] Class file not found. Looked for files with 'class' in their names under search dirs.")
            print("Please upload/put class.csv or class.xlsx into one of these folders:", self.search_dirs)
            return None
        if not self.aux_json.exists():
            print(f"[ERROR] Auxiliary JSON not found at {self.aux_json}")
            return None

        zoo_df = self._read_any_table(zoo_file)
        if zoo_df is None:
            print(f"[ERROR] Could not load zoo file: {zoo_file}")
            return None

        class_df = self._read_any_table(class_file)
        if class_df is None:
            print(f"[ERROR] Could not load class file: {class_file}")
            return None

        # Load and normalize auxiliary JSON
        try:
            with open(self.aux_json, "r", encoding="utf-8") as fh:
                raw_aux = json.load(fh)
        except Exception as ex:
            print(f"[ERROR] Failed to read auxiliary JSON {self.aux_json}: {ex}")
            return None

        aux_norm = [self._normalize_aux_record(r) for r in raw_aux]
        aux_df = pd.DataFrame(aux_norm)

        # Normalize animal name columns in zoo and class
        def pick_name_col(df: pd.DataFrame) -> str:
            for c in df.columns:
                if "animal" in c.lower() or "name" in c.lower():
                    return c
            return df.columns[0]

        zoo_name_col = pick_name_col(zoo_df)
        class_name_col = pick_name_col(class_df)

        zoo_df = zoo_df.copy()
        class_df = class_df.copy()
        zoo_df["animal_name"] = zoo_df[zoo_name_col].astype(str).str.strip().str.lower()
        class_df["animal_name"] = class_df[class_name_col].astype(str).str.strip().str.lower()

        # Merge: zoo primary (left join)
        class_drop = class_df.drop(columns=[class_name_col], errors="ignore")
        merged = zoo_df.merge(class_drop, on="animal_name", how="left", suffixes=("_zoo", "_class"))

        # Merge auxiliary (left join)
        merged = merged.merge(aux_df, on="animal_name", how="left")

        # Drop rows missing any auxiliary field
        aux_cols = ["habitat", "diet", "conservation_status"]
        before = merged.shape[0]
        merged_after = merged.dropna(subset=aux_cols).reset_index(drop=True).copy()
        after = merged_after.shape[0]

        # Save merged CSV if possible (silently fallback to local)
        out_path = Path("/mnt/data/merged_zoo_class_auxiliary_alpha.csv")
        try:
            merged_after.to_csv(out_path, index=False)
        except Exception:
            merged_after.to_csv("merged_zoo_class_auxiliary_alpha.csv", index=False)

        self.merged_data = merged_after
        print(f"[INFO] Merged rows before drop: {before}, after drop: {after}")
        return self.merged_data

    # Feature engineering method
    def alpha_engineer_features(self) -> Optional[pd.DataFrame]:
        """Engineer is_endangered and diet_complexity, print required outputs, save final CSV.
        Returns final DataFrame or None."""
        if self.merged_data is None:
            print("[ERROR] No merged data available. Run alpha_load_and_integrate() successfully first.")
            return None

        df = self.merged_data.copy()
        df["conservation_status"] = df.get("conservation_status", pd.Series([None] * len(df))).astype(str).str.strip().str.lower().replace({"nan": None})
        df["diet"] = df.get("diet", pd.Series([None] * len(df))).astype(str).str.strip().str.lower().replace({"nan": None})

        endangered_set = {"vulnerable", "endangered", "critically endangered"}
        df["is_endangered"] = df["conservation_status"].apply(lambda x: 1 if isinstance(x, str) and x in endangered_set else 0)

        def diet_complexity_map(d):
            if not isinstance(d, str):
                return 0
            if "carnivore" in d:
                return 3
            if "omnivore" in d:
                return 2
            return 0

        df["diet_complexity"] = df["diet"].apply(diet_complexity_map)

        # Save final CSV
        final_out = Path("/mnt/data/merged_with_engineered_features_alpha.csv")
        try:
            df.to_csv(final_out, index=False)
            saved = str(final_out)
        except Exception:
            df.to_csv("merged_with_engineered_features_alpha.csv", index=False)
            saved = "merged_with_engineered_features_alpha.csv"

        # Print required outputs exactly as requested
        print(f"Dataset shape: {df.shape}")
        print(f"Missing values: {df.isnull().sum().sum()}")
        print(f"Duplicate rows: {df.duplicated().sum()}")
        print("\nFirst 3 rows:")
        print(df.head(3))
        engineered_feature_names = ["is_endangered", "diet_complexity"]
        print(f"\nEngineered features: {list(engineered_feature_names)}")

        print(f"[INFO] Final result saved to: {saved}")
        self.merged_data = df
        return df



