"""Result AK: the preregistered ghost test at 0.10 (Preregistration AK, committed before this run).
The Result AH and AH2 tools are imported unchanged; only SCORE is assigned. Their header lines
name 0.30 literally; the banner above each block is the operating point run."""
import importlib.util
import pathlib
import sys

here = pathlib.Path(__file__).parent


def main():
    for tool in ("result_ah_ghost_coincidence", "result_ah2_ghost_persistence"):
        print("\n" + "#" * 92); print(f"# RESULT AK  score >= 0.10  ::  {tool} (imported unchanged, SCORE assigned)"); print("#" * 92, flush=True)
        spec = importlib.util.spec_from_file_location(tool, here / f"{tool}.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.SCORE = 0.10
        m.main()
    print("\n" + "-" * 92)
    print("NON-CLAIMS: preregistered replication of Results AH and AH2 at 0.10; every caveat of those")
    print("results applies. No detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
