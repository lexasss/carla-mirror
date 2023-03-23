from src.app import App

if __name__ == '__main__':
    try:
        App().run()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    else:
        print('done.')
