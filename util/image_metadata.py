import os
from io import BytesIO
from typing import Union

from PIL import Image


def extract_metadata(image_input: Union[str, BytesIO], filename: str = None):
    if isinstance(image_input, str):
        image = Image.open(image_input)
        image_size_mb = round(os.path.getsize(image_input) / (1024 * 1024), 2)
        if not filename:
            filename = os.path.basename(image_input)
    elif isinstance(image_input, BytesIO):
        image = Image.open(image_input)
        image_input.seek(0)
        image_size_mb = round(len(image_input.getbuffer()) / (1024 * 1024), 2)

        metadata_dict = {}
        metadata_text = image.info.get('parameters', '')

        if not metadata_text:
            # If no metadata, save image properties and exit
            metadata_dict = {
                "Filename": filename,
                "Size": f"{image_size_mb} MB",
                "Dimensions": f"{image.size[0]}x{image.size[1]}",
                "Format": image.format,
                "Mode": image.mode
            }
        else:
            for line in metadata_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata_dict[key.strip()] = value.strip()
                else:
                    if 'parameters' in metadata_dict:
                        metadata_dict['parameters'] += f"\n{line.strip()}"
                    else:
                        metadata_dict['parameters'] = line.strip()

            # Special handling for the "Steps" line
            if 'Steps' in metadata_dict:
                steps_value = metadata_dict['Steps']
                steps_dict = {}
                for item in steps_value.split(','):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        steps_dict[key.strip()] = value.strip()
                    else:
                        steps_dict['Steps'] = item.strip()
                metadata_dict['details'] = steps_dict
                del metadata_dict['Steps']

            # Add image properties to metadata dictionary
            metadata_dict.update({
                "Filename": filename,
                "Size": f"{image_size_mb} MB",
                "Dimensions": f"{image.size[0]}x{image.size[1]}",
                "Format": image.format,
                "Mode": image.mode
            })

        return metadata_dict
