import pygame

from copy import copy

from .errors import NoActiveSceneError, NotImplementedError
from .math import Vector

class Client:
    def __init__(
        self,
        window_name: str,
        window_size: Vector,
        window_icon: pygame.Surface = None,
        resizeable_window: bool = True,
        keep_aspect_ratio: bool = True
    ) -> None:
        """
        The game's main client

        Parameters:
            window_name: the window's name
            window_size: the window size
        """
        self.is_running = True # bool
        self._window_name = window_name # str
        self.original_window_size = window_size # Vector
        self.window_icon = window_icon
        self.keep_aspect_ratio = keep_aspect_ratio # bool
        self.original_aspect_ratio = window_size.ratio_xy # float
        
        self.running_scenes = {}
        self.scene_manager = None # SceneManager
        
        self.pg_clock = pygame.time.Clock()
        self.max_fps = -1 # int
        self.delta_time = 0

        self.pg_flag = 0
        if resizeable_window:
            self.pg_flag = pygame.RESIZABLE

        self.window = pygame.display.set_mode(
            (window_size.x, window_size.y),
            self.pg_flag
        )
        self.screen = pygame.Surface((window_size.x, window_size.y))

        pygame.display.set_caption(self._window_name)

        if self.window_icon is None:
            pass # add sakuya as a default icon

        if self.window_icon is not None:
            pygame.display.set_icon(self.window_icon)

    @property
    def window_name(self) -> str:
        return self._window_name

    @window_name.setter
    def window_name(self, value: str) -> None:
        self._window_name = value
        pygame.display.set_caption(self._window_name)

    @property
    def window_size(self) -> Vector:
        window_rect = self.window.get_rect()
        return Vector(window_rect.width, window_rect.height)

    @property
    def current_fps(self) -> float:
        return self.pg_clock.get_fps()

    def main(self) -> None:
        """
        Main game loop
        """
        while(self.is_running):
            if self.running_scenes == []:
                raise NoActiveSceneError

            if self.keep_aspect_ratio:
                pg_event = pygame.event.get(
                    eventtype=pygame.VIDEORESIZE,
                    pump=True
                )
                if pg_event != []:
                    self.window = pygame.display.set_mode((
                        pg_event[0].w, 
                        pg_event[0].w * self.original_window_size.ratio_yx),
                        self.pg_flag
                    )

            for s in self.running_scenes:
                s = self.running_scenes[s]["scene"]
                if s.is_paused:
                    s.update()
            
            screen = pygame.transform.scale(self.screen, (self.window_size.x, self.window_size.y))
            self.window.blit(screen, (0,0))
            self.delta_time = self.pg_clock.tick(self.max_fps) / 1000
            pygame.display.flip()

    def add_scene(self, scene_name: str, **kwargs) -> None:
        """
        Adds scene to running scene 

        Parameters:
            scene_name: str to be added
        """
        scene = self.scene_manager.get_scene(scene_name)
        scene.on_awake(**kwargs)
        self.running_scenes[scene.name] = {"scene": scene, "kwargs": kwargs}

    def remove_scene(self, scene_name: str, **kwargs) -> None:
        """
        Removes scene

        Parameters:
            scene_name: str to be removed
        """
        scene = self.scene_manager.get_scene(scene_name)
        scene.on_delete(**kwargs)
        del self.running_scenes[scene.name]

    def replace_scene(
        self,
        old_scene_name: str,
        new_scene_name: str, 
        **kwargs
    ) -> None:
        """
        Removes and adds a scene

        Parameters:
            scene_name: str to be added
        """
        old_scene = self.scene_manager.get_scene(old_scene_name)
        new_scene = self.scene_manager.get_scene(new_scene_name)
        self.remove_scene(old_scene)
        self.add_scene(new_scene, **kwargs)