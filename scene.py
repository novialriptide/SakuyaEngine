from .client import Client
from .entity import Entity
from .errors import EntityNotInScene
from .events import EventSystem

from typing import List

class Scene:
    def __init__(self, client: Client, **kwargs) -> None:
        """
        The base class for a scene

        This class must be inherited by another class in order to work properly.

        Parameters:
            client: game client
        """
        self.is_paused = True
        self.client = client
        self.entities = []
        self.event_system = EventSystem()
        self.kwargs = kwargs

    @property
    def name(self) -> str:
        return __class__.__name__

    def on_awake(self, **kwargs) -> None:
        """
        Will be called upon startup.
        
        Must be overrided
        """
        pass

    def on_delete(self, **kwargs) -> None:
        """
        Will be called upon destruction.
        
        Must be overrided
        """
        pass

    def update(self, delta_time, **kwargs) -> None:
        """
        Will be called upon every frame. Calling advance_frame() is recommended.
        
        Must be overrided.

        """
        pass

    def find_entities_by_name(self, name: str) -> List[Entity]:
        """
        Finds all registered entities in this scene

        Parameters:
            name: Name of the entity

        """
        entities = []
        for o in self.entities:
            if o.name == name:
                entities.append(o)

        return entities

    def test_collisions(self, entity: Entity) -> List[Entity]:
        entities = self.entities[:] # copies the list
        try:
            entities.remove(entity)
        except:
            raise EntityNotInScene
        
        collided = []
        for e in entities:
            if entity.hitbox.colliderect(e.hitbox):
                collided.append(e)

        return collided

    def advance_frame(self, delta_time: float) -> None:
        """
        Updates the entities inside the world, such as 
        physics & animation
        
        Should be added to the end of the main loop

        """
        for object in self.entities[:]:
            object.update(delta_time)
            if object._is_destroyed:
                self.entities.remove(object)

class SceneManager:
    def __init__(self, client: Client) -> None:
        """
        The scene manager which is used to register scenes

        Parameters:
            client: game client

        """
        client.scene_manager = self
        self.client = client
        self.registered_scenes = {}

    def register_scene(self, scene: Scene) -> bool:
        """
        Registers a scene into the scene manager

        Parameters:
            scene: scene to be registered

        """
        instance = scene(self.client)
        self.registered_scenes[scene.__name__] = instance

    def get_scene(self, scene_name: str) -> Scene:
        return self.registered_scenes[scene_name]