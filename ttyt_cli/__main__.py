from .main import main

try:
    main()
except KeyboardInterrupt:
    import sys
    sys.exit(130)
