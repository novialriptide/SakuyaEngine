"""
SakuyaEngine (c) 2020-2021 Andrew Hong
This code is licensed under GNU LESSER GENERAL PUBLIC LICENSE (see LICENSE for details)
"""
from copy import copy
from typing import TypeVar, Callable

import pygame
import time

from .clock import Clock
from .errors import NoActiveSceneError, SceneNotActiveError
from .events import EventSystem
from .sounds import SoundManager
from .scene import SceneManager

pygame_vector2 = TypeVar("pygame_vector2", Callable, pygame.Vector2)

__all__ = ["Client"]


class Client:
    def __init__(
        self,
        window_name: str,
        window_size: pygame_vector2,
        window_icon: pygame.Surface = None,
        resizeable_window: bool = True,
        scale_upon_startup: float = 1,
        debug_caption: bool = True,
        keep_aspect_ratio: bool = True,
        mouse_image: pygame.Surface = None,
    ) -> None:
        """The game's main client.

        Warning: An event system is already built in to this object, but
        do not use it for any events related to a scene. Only use it
        for notifications, client-sided messages, etc.

        Parameters:
            window_name: the window's name
            window_size: the window size
        """
        self.debug_caption = debug_caption
        self.is_running = True  # bool
        self.clock = Clock()
        self.event_system = EventSystem(self.clock)
        self._window_name = window_name  # str
        self._screen_pos = pygame.Vector2(0, 0)
        self.original_window_size = window_size  # pygame.Vector2
        self.window_icon = window_icon
        self.original_aspect_ratio = window_size.x / window_size.y  # float
        self.keep_aspect_ratio = keep_aspect_ratio
        self.mouse_image = mouse_image

        self.running_scenes = {}
        self.deleted_scenes_queue = []
        self.scene_manager = SceneManager(self)

        self.sound_manager = SoundManager(self)

        self.pg_clock = pygame.time.Clock()
        self.max_fps = -1  # int
        self.delta_time = 0
        self.raw_delta_time = 0
        self.delta_time_modifier = 1

        self.pg_flag = 0
        if resizeable_window:
            self.pg_flag = pygame.RESIZABLE

        self.screen = pygame.Surface(window_size)  # lgtm [py/call/wrong-arguments]
        self.window_size = window_size * scale_upon_startup

        pygame.display.set_caption(self._window_name)

        if self.mouse_image is not None:
            pygame.mouse.set_cursor(
                (8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)
            )

        if self.window_icon is None:
            pass  # add sakuya as a default icon

        if self.window_icon is not None:
            # if you run the program from source, the icon
            # won't show up until you compile the program.
            pygame.display.set_icon(self.window_icon)

        self.events = []

    @property
    def window_name(self) -> str:
        return self._window_name

    @window_name.setter
    def window_name(self, value: str) -> None:
        self._window_name = value
        pygame.display.set_caption(self._window_name)

    @property
    def window_size(self) -> pygame.Vector2:
        return pygame.Vector2(self.window.get_size())

    @window_size.setter
    def window_size(self, value) -> None:
        self.window = pygame.display.set_mode((value.x, value.y), self.pg_flag)

    @property
    def screen_size(self) -> pygame.Vector2:
        return pygame.Vector2(
            self.window_size.y
            * self.original_window_size.x
            / self.original_window_size.y,
            self.window_size.y,
        )

    @property
    def _screen(self) -> pygame.Surface:
        return pygame.transform.scale(self.screen, self.screen_size)

    @property
    def scale(self) -> pygame.Vector2:
        return pygame.Vector2(
            (self.window_size.x - self._screen_pos.x * 2) / self.original_window_size.x,
            (self.window_size.y - self._screen_pos.y * 2) / self.original_window_size.y,
        )

    @property
    def mouse_pos(self) -> pygame.Vector2:
        scale = self.scale
        mouse_pos = pygame.mouse.get_pos()
        scaled_pos = pygame.Vector2(
            (mouse_pos[0] - self._screen_pos.x) / scale.x,
            (mouse_pos[1] - self._screen_pos.y) / scale.y,
        )
        return scaled_pos

    @property
    def current_fps(self) -> float:
        return self.pg_clock.get_fps()

    def main(self) -> None:
        """
        Main game loop
        """
        while self.is_running:
            # Delta time
            self.raw_delta_time = self.pg_clock.tick(self.max_fps) / 1000 * self.max_fps
            print(self.raw_delta_time)
            self.clock.speed = self.delta_time_modifier
            self.delta_time = self.raw_delta_time * self.delta_time_modifier

            if self.running_scenes == []:
                raise NoActiveSceneError

            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.VIDEORESIZE:
                    if self.keep_aspect_ratio:
                        new_height = (
                            event.w
                            * self.original_window_size.y
                            / self.original_window_size.x
                        )
                        self.window = pygame.display.set_mode(
                            (event.w, new_height), self.pg_flag
                        )
                    window_rect = self.window.get_rect()
                    screen_rect = self._screen.get_rect()
                    self._screen_pos = pygame.Vector2(
                        window_rect.centerx - screen_rect.centerx,
                        window_rect.centery - screen_rect.centery,
                    )

            # Update all scenes
            for s in copy(self.running_scenes):
                s = self.running_scenes[s]["scene"]
                if not s.paused:
                    s.update()
                    s.clock.speed = self.delta_time_modifier
                    self.screen.fill((191, 64, 191))
                    self.screen.blit(s.screen, s.screen_pos)

            # Delete scenes in queue
            for s in self.deleted_scenes_queue[:]:
                try:
                    self.deleted_scenes_queue.remove(s)
                    del self.running_scenes[s]
                except KeyError:
                    print(f'Tried deleting scene that does not exist: "{s}"')

            if self.mouse_image is not None and self.mouse_pos:
                self.screen.blit(self.mouse_image, self.mouse_pos)

            self.window.blit(self._screen, self._screen_pos)

            self.event_system.update()
            pygame.display.update()

            if self.debug_caption:
                fps = round(self.pg_clock.get_fps(), 2)
                bullets = 0
                entities = 0
                effects = 0
                scene_time = 0
                client_time = round(self.clock.get_time(), 2)
                for s in self.running_scenes:
                    s = self.running_scenes[s]["scene"]
                    bullets += len(s.bullets)
                    entities += len(s.entities)
                    effects += len(s.effects)
                    scene_time = round(s.clock.get_time(), 2)
                scene = ", ".join(self.running_scenes)
                pygame.display.set_caption(
                    f"fps: {fps}, entities: {entities + bullets}, effects: {effects}, scene_time: {scene_time}, client_time: {client_time}, scene: {scene}"
                )

    def add_scene(self, scene_name: str, **kwargs) -> None:
        """Adds scene to running scene

        Parameters:
            scene_name: str to be added

        """
        scene = copy(self.scene_manager.get_scene(scene_name))(self)
        scene.on_awake(**kwargs)
        self.running_scenes[scene.name] = {"scene": scene, "kwargs": kwargs}

    def remove_scene(self, scene_name: str, **kwargs) -> None:
        """Removes scene

        Parameters:
            scene_name: str to be removed

        """
        try:
            scene = self.running_scenes[scene_name]["scene"]
            scene.on_delete(**kwargs)
            self.deleted_scenes_queue.append(scene.name)
        except KeyError:
            raise SceneNotActiveError

    def replace_scene(self, old_scene_name: str, new_scene_name: str, **kwargs) -> None:
        """Removes and adds a scene

        Parameters:
            scene_name: str to be added

        """
        try:
            self.remove_scene(old_scene_name)
            self.add_scene(new_scene_name, **kwargs)
        except KeyError:
            raise SceneNotActiveError
