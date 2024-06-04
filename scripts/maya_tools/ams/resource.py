from dataclasses import dataclass
from core.core_enums import FileExtension, ResourceType
from maya_tools.ams.ams_enums import ItemStatus


@dataclass
class Resource:
    name: str
    scene_extension: FileExtension
    export_extension: FileExtension
    resource_type: ResourceType
    status: ItemStatus

    def __repr__(self) -> str:
        return f'{self.scene_file_name} [{self.resource_type.name}] [{self.status.name}]'

    @property
    def scene_file_name(self) -> str:
        return f'{self.name}{self.scene_extension.value}'

    @property
    def export_file_name(self) -> str:
        return f'{self.name}{self.export_extension.value}'


if __name__ == '__main__':
    resource = Resource(name='clairee',
                        scene_extension=FileExtension.mb,
                        export_extension=FileExtension.fbx,
                        resource_type=ResourceType.scene,
                        status=ItemStatus.export)
    print(resource)
