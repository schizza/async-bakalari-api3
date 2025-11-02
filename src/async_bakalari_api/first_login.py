"""First login - for demo only."""

from .bakalari import Bakalari, Schools


async def first_login():
    """Perform the first login for the demo."""
    schools: Schools = Schools().load_from_file("schools_data.json")  # pyright: ignore[]

    bakalari = Bakalari(
        schools.get_url("Your school"),  # pyright: ignore[]
        auto_cache_credentials=True,
        cache_filename="new_data.json",
    )
    await bakalari.first_login("username", "password")
