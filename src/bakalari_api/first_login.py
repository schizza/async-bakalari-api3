from .bakalari import Bakalari, Schools


async def first_login():
    schools: Schools = Schools().load_from_file("schools_data.json")

    bakalari = Bakalari(
        schools.get_url("Kadaňaká"),
        auto_cache_credentials=True,
        cache_filename="new_data.json",
    )
    await bakalari.first_login("Svobo78361", "0DPmd0W8")
