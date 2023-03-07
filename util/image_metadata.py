from PIL import Image
import json
import os


def extract_metadata(image_path):
    """
    It opens the image file, parses the metadata, and returns a dictionary of the metadata

    :param image_path: The path to the image file
    :return: A dictionary of metadata
    """
    # Open the image file
    image = Image.open(image_path)

    # Parse the metadata
    metadata_dict = {}
    metadata_text = image.info.get('parameters', '')

    # Convert image.size to MB
    image_size_mb = round(os.path.getsize(image_path) / (1024 * 1024), 2)

    if not metadata_text:
        # If no metadata, save image properties and exit
        metadata_dict = {
            "Filename": os.path.basename(image_path),
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
            "Filename": os.path.basename(image_path),
            "Size": f"{image_size_mb} MB",
            "Dimensions": f"{image.size[0]}x{image.size[1]}",
            "Format": image.format,
            "Mode": image.mode
        })

    return metadata_dict


# # Calling the function extract_metadata() and passing the image file name as an argument.
# metadata_dict = extract_metadata("11366-2854177017-gigantic20breasts_1.png")
#
# # Opening a file called metadata.json and writing the metadata_dict to it.
# with open('metadata.json', 'w') as f:
#     json.dump(metadata_dict, f, indent=4)
