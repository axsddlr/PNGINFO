import os
from io import BytesIO
from typing import Union

from PIL import Image
from discord import Embed


def extract_metadata(
    image_input: Union[str, BytesIO], image: Image, filename: str = None
):
    """
    This function extracts metadata from an image file or bytes object and returns it as a dictionary,
    along with the image and filename.

    :param image_input: The input image file, which can be either a string representing the file path or
    a BytesIO object representing the image data
    :type image_input: Union[str, BytesIO]
    :param image: The `image` parameter is an instance of the `Image` class, which represents the image
    that is being processed. It contains the pixel data, size, format, and other metadata of the image.
    This parameter is used to extract metadata from the image, such as its size, format, and
    :type image: Image
    :param filename: The `filename` parameter is an optional string that represents the name of the
    image file. It can be used to provide a custom name for the image file when it is saved or to
    extract metadata specific to the file name. If no filename is provided, the function will attempt to
    extract the filename from
    :type filename: str
    """
    if isinstance(image_input, str):
        image_size_mb = round(os.path.getsize(image_input) / (1024 * 1024), 2)
        if not filename:
            filename = os.path.basename(image_input)
    elif isinstance(image_input, BytesIO):
        image_input.seek(0)
        image_size_mb = round(len(image_input.getbuffer()) / (1024 * 1024), 2)

    metadata_text = read_info_from_image_stealth(image)

    if not metadata_text:
        metadata_dict = {
            "Filename": filename,
            "Size": f"{image_size_mb} MB",
            "Dimensions": f"{image.size[0]}x{image.size[1]}",
            "Format": image.format,
            "Mode": image.mode,
        }
    else:
        metadata_dict = get_parameters(metadata_text)
        metadata_dict.update(
            {
                "Filename": filename,
                "Size": f"{image_size_mb} MB",
                "Dimensions": f"{image.size[0]}x{image.size[1]}",
                "Format": image.format,
                "Mode": image.mode,
            }
        )
    return metadata_dict


def get_parameters(param_str):
    """
    The function "get_parameters" takes a string as input and does not have any implementation yet.

    :param param_str: The parameter `param_str` is a string that contains a set of parameters separated
    by a delimiter. The function `get_parameters` is expected to parse this string and return a list of
    individual parameters
    """
    output_dict = {}
    parts = param_str.split("Steps: ")
    prompts = parts[0]
    params = "Steps: " + parts[1]
    if "Negative prompt: " in prompts:
        output_dict["Prompt"] = prompts.split("Negative prompt: ")[0]
        output_dict["Negative Prompt"] = prompts.split("Negative prompt: ")[1]
    else:
        output_dict["Prompt"] = prompts

    params = params.split(", ")
    for param in params:
        try:
            key, value = param.split(": ")
            output_dict[key] = value
        except ValueError:
            pass
    return output_dict


def get_embed(embed_dict, context):
    """
    The function "get_embed" takes in an embed dictionary and context as parameters.

    :param embed_dict: It seems like the description of the parameters is incomplete. Can you provide
    more information about the function and the parameters?
    :param context: The context parameter is a variable that represents the current state or environment
    in which the function is being executed. It can be used to pass additional information or data to
    the function that may be needed to perform its task. In this case, it is not clear what the context
    parameter is used for without seeing
    """
    embed = Embed()

    for key, value in embed_dict.items():
        if key in ["Prompt", "Negative Prompt"]:
            if len(value) <= 1024:
                embed.add_field(name=key, value=value, inline=False)
            else:
                # Split long text into multiple fields
                for i, chunk in enumerate(
                    value[i : i + 1024] for i in range(0, len(value), 1024)
                ):
                    field_name = f"{key} (part {i + 1})"
                    embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name=key, value=value, inline=True)

    embed.add_field(
        name="Original Message", value=f"[Click here]({context.jump_url})", inline=False
    )

    embed.set_footer(
        text=f"Requested by {context.author}", icon_url=context.author.avatar.url
    )
    return embed


def read_info_from_image_stealth(image):
    """
    This function reads information from a given image using a specific encoding scheme.

    :param image: The input image from which information needs to be extracted
    :return: a string variable named "geninfo" which contains the decoded data extracted from the input
    image.
    """
    width, height = image.size
    pixels = image.load()

    binary_data = ""
    buffer = ""
    index = 0
    sig_confirmed = False
    confirming_signature = True
    reading_param_len = False
    reading_param = False
    read_end = False
    geninfo = ""
    for x in range(width):
        for y in range(height):
            pixel_data = pixels[x, y]
            if len(pixel_data) == 3:
                r, g, b = pixel_data
                a = 255
            else:
                r, g, b, a = pixel_data
            buffer += str(a & 1)
            if confirming_signature:
                if index == len("stealth_pnginfo") * 8 - 1:
                    if buffer == "".join(
                        format(byte, "08b")
                        for byte in "stealth_pnginfo".encode("utf-8")
                    ):
                        confirming_signature = False
                        sig_confirmed = True
                        reading_param_len = True
                        buffer = ""
                        index = 0
                    else:
                        read_end = True
                        break
            elif reading_param_len:
                if index == 32:
                    param_len = int(buffer, 2)
                    reading_param_len = False
                    reading_param = True
                    buffer = ""
                    index = 0
            elif reading_param:
                if index == param_len:
                    binary_data = buffer
                    read_end = True
                    break
            else:
                # impossible
                read_end = True
                break

            index += 1
        if read_end:
            break

    if sig_confirmed and binary_data != "":
        # Convert binary string to UTF-8 encoded text
        decoded_data = bytearray(
            int(binary_data[i : i + 8], 2) for i in range(0, len(binary_data), 8)
        ).decode("utf-8", errors="ignore")

        geninfo = decoded_data

    return geninfo
