from functools import partial
from gpiozero import Button
import pygame, time, os


OK_EVENT = pygame.USEREVENT+1
BACK_EVENT = pygame.USEREVENT+2

PIN_DOWN = {'State':'Down'}
PIN_UP = {'State':'UP'}


def post_event(event, sentinel=[]):
    pygame.event.post(event)


def main():
    # this needs to come *before* the
    # buttons are created, as otherwise we get a
    # race condition when events are being triggered
    # before the system is initialized.
    pygame.display.init()

    ok = Button(24) #(ok/feuer)
    back = Button(25) #(zurueck/menue)
    ok.when_pressed = lambda _e: pygame.event.post(pygame.event.Event(OK_EVENT, PIN_UP))
    ok.when_released = lambda _e: pygame.event.post(pygame.event.Event(OK_EVENT, PIN_DOWN))

    screen = pygame.display.set_mode((400,400))

    pygame.init()

    clock = pygame.time.Clock()

    while True:
        print('tick')
        pygame.display.update()
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == OK_EVENT:
                print 'Feuer!'
                print(event.State)

        clock.tick(10)


if __name__ == '__main__':
    main()
