"""Console entry point: `tollfree "prompt"` to chat, `tollfree probe` to check keys."""

import sys

from .probe import probe_all
from .router import chat


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] == "probe":
        probe_all()
        return

    q = " ".join(argv) or "Say hello in one short sentence."
    answer, meta = chat(q, return_meta=True, verbose=True)
    print(f"\n--- {meta['provider']} / {meta['model']} ---")
    print(answer)


if __name__ == "__main__":
    main()
