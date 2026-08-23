from channel.prompts import strip_image_brands


def test_strip_image_brands_removes_spoken_names():
    text = "A laptop showing Grok next to an OpenAI door and a SpaceX hangar."
    out = strip_image_brands(text)
    assert "Grok" not in out
    assert "OpenAI" not in out
    assert "SpaceX" not in out
    assert "laptop" in out
