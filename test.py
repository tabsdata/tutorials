# Python Typing Text Effect - adapted to show a VSCode-like code window
import time, os, sys

# ANSI colors approximating VSCode Dark Plus
RESET = "\033[0m"
BG = "\033[48;2;30;30;30m"           # editor background #1E1E1E
FG = "\033[38;2;220;220;220m"        # default foreground
PURPLE = "\033[38;2;197;134;192m"    # decorators and keywords
LB = "\033[38;2;156;220;254m"        # identifiers
TEAL = "\033[38;2;78;201;176m"       # class names and types
YEL = "\033[38;2;220;220;170m"       # function names
STR = "\033[38;2;206;145;120m"       # strings
DIM = "\033[2m\033[38;2;133;133;133m"  # line numbers and UI chrome

def typingPrint(text, delay=0.01):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)

def clearScreen():
    os.system("clear" if os.name != "nt" else "cls")

def ln(n):
    return f"{DIM}{str(n).rjust(2)} {RESET}"

code_lines = [
    "\n\n\n\n\n\n\n",
    # 1
    ln(1)  + PURPLE + "@td.publisher" + RESET  + "(" + RESET + "\n",
    # 2
    ln(2)  + "    " + LB + "source" + RESET  + "=" + LB + "td" + RESET + "." + TEAL + "MySQLSource" + RESET  + "(" + RESET + "\n",
    # 3
    ln(3)  + "        " + LB + "uri" + RESET  + "=" + LB + "MYSQL_URI" + RESET  + "," + RESET + "\n",
    # 4
    ln(4)  + "        " + LB + "query" + RESET  + "=[" + STR + "\"SELECT * FROM raw_customer_data\"" + RESET  + "]," + RESET + "\n",
    # 5
    ln(5)  + "        " + LB + "credentials" + RESET  + "=" + LB + "td" + RESET + "." + TEAL + "UserPasswordCredentials" + RESET  + "(" + LB + "MYSQL_USERNAME" + RESET  + ", " + LB + "MYSQL_PASSWORD" + RESET  + ")," + RESET + "\n",
    # 6
    ln(6)  + "    " + RESET  + ")," + RESET + "\n",
    # 7
    ln(7)  + "    " + LB + "tables" + RESET  + "=[" + STR + "\"raw_customer_data\"" + RESET  + "]," + RESET + "\n",
    # 8
    ln(8)  + ")" + RESET + "\n",
    # 9
    ln(9)  + PURPLE + "def" + RESET + " " + YEL + "mysql_pub" + RESET + "(" + LB + "tf1" + RESET + ": " + LB + "td" + RESET + "." + TEAL + "TableFrame" + RESET + "):" + "\n",
    # 10
    ln(10)  + "    " + PURPLE + "return" + RESET + " " + LB + "tf1" + RESET + "\n",
]

def main():
    clearScreen()
    for line in code_lines:
        typingPrint(line, 0.002)
    print(RESET)
    time.sleep(1)
    # fake terminal run
    typingPrint(f"{DIM}$ python demo.py{RESET}\n", 0.5)
    time.sleep(0.5)
    typingPrint("mysql_pub registered\n", 0.02)

if __name__ == "__main__":
    main()