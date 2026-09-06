"""Result AN: the preregistered test of the same-kind ordering in the inflation quantity at 0.20
and 0.40 (Preregistration AN, committed before this run). Result AF imported unchanged; only SCORE
assigned. The imported tool's non-claims line names 0.30 literally; the banner is the point run."""
import importlib.util
import pathlib
import sys

here = pathlib.Path(__file__).parent


def main():
    for score in (0.20, 0.40):
        print("\n" + "#" * 92); print(f"# RESULT AN  score >= {score:.2f}  ::  result_af_sensor_jury (imported unchanged, SCORE assigned)"); print("#" * 92, flush=True)
        spec = importlib.util.spec_from_file_location("af", here / "result_af_sensor_jury.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.SCORE = score
        m.main()
    print("\n" + "-" * 92)
    print("NON-CLAIMS: preregistered replication of Result AF at two operating points; every caveat of")
    print("Result AF applies. No detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
