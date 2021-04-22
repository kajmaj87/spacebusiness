class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class emoji:
    FOOD = '\U0001F37D '
    FACTORY = '\U0001F3ED'
    HOURGLASS = '\U000023F3'
    SHOPPING_CART = '\U0001F6D2'
    EXCHANGE = '\U0001F4B1'
    CANCEL = '❌'
    MONEY_BAG = '\U0001F4B0'

def printHeader(output):
    print("\n" + bcolors.HEADER + bcolors.BOLD + output + bcolors.END)

def printSummary(output):
    print("\n" + bcolors.OKCYAN + bcolors.UNDERLINE + bcolors.BOLD + output + bcolors.END)

def printIntro(output):
    print("\n" + bcolors.WARNING + bcolors.UNDERLINE + bcolors.BOLD + output + bcolors.END)