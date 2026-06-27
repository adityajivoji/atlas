#!/usr/bin/env python
import sys
from alembic.config import Config
import alembic.command as command
from settings import PostgresSettings

ALEMBIC_CONFIG = "alembic.ini"

USAGE = """
Usage:
  python db.py upgrade [REVISION]         # default: head
  python db.py downgrade [REVISION]       # default: -1
  python db.py migrate [-m "msg"] [--autogenerate]
  python db.py current
  python db.py history

Examples:
  python db.py upgrade head
  python db.py downgrade -1
  python db.py migrate -m "create users table" --autogenerate
  python db.py migrate --autogenerate   # no message
  python db.py current
  python db.py history
"""

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(USAGE)
        sys.exit(0)

    command_name = sys.argv[1]
    args = sys.argv[2:]

    cfg = Config(ALEMBIC_CONFIG)
    cfg.set_main_option("sqlalchemy.url", str(PostgresSettings().POSTGRES_MIGRATION_URL))
    cfg.set_main_option("sqlalchemy.echo", "true")
    
    

    if command_name == "upgrade":
        revision = args[0] if args else "head"
        command.upgrade(cfg, revision)

    elif command_name == "downgrade":
        revision = args[0] if args else "-1"
        command.downgrade(cfg, revision)

    elif command_name == "migrate":
        # Default options
        msg = None
        autogen = True

        # Parse args
        if "-m" in args:
            idx = args.index("-m")
            if idx + 1 < len(args):
                msg = args[idx + 1]

        # Always create a revision (like the bash script)
        command.revision(cfg, message=msg, autogenerate=autogen)

    elif command_name == "current":
        command.current(cfg)

    elif command_name == "history":
        command.history(cfg)

    else:
        print(f"Unknown command: {command_name}\n")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
