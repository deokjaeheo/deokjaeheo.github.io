"""Legacy command alias. Publications are now curated manually; no Scholar requests."""
import argparse
from render_publications import main, render
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-only',action='store_true')
    args=parser.parse_args()
    if not args.render_only:
        parser.error('Automatic Scholar updates are disabled. Edit curated data and run render_publications.py.')
    main()
