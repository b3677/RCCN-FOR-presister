import importlib
import sys


def main():
    required_modules = [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "sklearn",
        "umap",
        "openpyxl",
        "pytest",
    ]
    missing = []
    for module_name in required_modules:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
            continue
        version = getattr(module, "__version__", "unknown")
        print(f"{module_name} {version}")

    if missing:
        print(
            "Missing required Python package(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "Install them in F:\\conda_envs\\e_coli_rpy2_py311 before the overnight run.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
