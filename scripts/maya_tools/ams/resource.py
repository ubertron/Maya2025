from dataclasses import dataclass
from core.core_enums import FileExtension, ResourceType
from maya_tools.ams.ams_enums import ItemStatus


@dataclass
class Resource:
    name: str
    extension: FileExtension
    resource_type: ResourceType
    status: ItemStatus

    def __repr__(self) -> str:
        return f'{self.file_name} [{self.resource_type.name}] [{self.status.name}]'

    @property
    def file_name(self) -> str:
        return f'{self.name}{self.extension.value}'


if __name__ == '__main__':
    resource = Resource(name='clairee',
                        extension=FileExtension.mb,
                        resource_type=ResourceType.scene,
                        status=ItemStatus.export)
    print(resource)
