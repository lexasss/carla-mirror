from src.app import App

if __name__ == '__main__':
    try:
        App().run()
    except KeyboardInterrupt:
        print('APP: Cancelled by user')
    else:
        print('APP: exit')
