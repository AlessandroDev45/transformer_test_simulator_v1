# analyze_callbacks.py
from utils.callback_analyzer import analyze_all_modules


def main():
    result = analyze_all_modules()
    print(f"Total callbacks: {result['total_callbacks']}")
    print(f"Duplicates found: {len(result['duplicates'])}")

    if result["duplicates"]:
        print("\nDuplicate callbacks:")
        for dup in result["duplicates"]:
            print(f"  Output: {dup['output']}")
            print(f"  Callbacks: {', '.join(dup['callbacks'])}")
            print(f"  Modules: {', '.join(dup['modules'])}")
            print()


if __name__ == "__main__":
    main()
