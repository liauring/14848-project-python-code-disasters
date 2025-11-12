def trigger_blocker():
    x = 12345
    # S5644: x is not subscriptable -> bug
    y = x[0]
    print(y)


if __name__ == "__main__":
    trigger_blocker()
