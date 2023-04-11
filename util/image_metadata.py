import os
from io import BytesIO
from typing import Union

from PIL import Image
from discord import Embed


def extract_metadata(
    image_input: Union[str, BytesIO], image: Image, filename: str = None
):
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
    output_dict = {}
    parts = param_str.split("Steps: ")
    prompts = parts[0]
    params = "Steps: " + parts[1]
    if "Negative prompt: " in prompts:
        output_dict["Prompt"] = prompts.split("Negative prompt: ")[0]
        output_dict["Negative Prompt"] = prompts.split("Negative prompt: ")[1]
        if len(output_dict["Negative Prompt"]) > 1000:
            output_dict["Negative Prompt"] = (
                output_dict["Negative Prompt"][:1000] + "..."
            )
    else:
        output_dict["Prompt"] = prompts
    if len(output_dict["Prompt"]) > 1000:
        output_dict["Prompt"] = output_dict["Prompt"][:1000] + "..."
    params = params.split(", ")
    for param in params:
        try:
            key, value = param.split(": ")
            output_dict[key] = value
        except ValueError:
            pass
    return output_dict


def get_embed(embed_dict, context):
    embed = Embed()

    for key, value in embed_dict.items():
        if key == "Prompt":
            embed.add_field(name=key, value=value, inline=False)
        elif key == "Negative Prompt":
            embed.add_field(name=key, value="\n" + value, inline=False)
        else:
            embed.add_field(name=key, value=value, inline=True)

    embed.set_footer(
        text=f"Requested by {context.author}", icon_url=context.author.avatar.url
    )
    return embed


def read_info_from_image_stealth(image):
    width, height = image.size
    pixels = image.load()

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    binary_data = ""
    buffer = ""
    index = 0
    sig_confirmed = False
    confirming_signature = True
    reading_param_len = False
    reading_param = False
    read_end = False
    for x in range(width):
        for y in range(height):
            _, _, _, a = pixels[x, y]
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
