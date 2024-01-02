
VISION_TOOL = "if image type is a photo, return venue name (usually, bigger text) and venue type (make your best bet). if image type is card, return captionized elements in the image. always return the response in json format. do not make up data."

AGENT_SYSTEM = "you are an expert in vCard format"
AGENT_TOOL = "convert previous json data to document type RFC 6350 using text representation. ignore logo and other decorations. be precise and concise. do not explain your output"
