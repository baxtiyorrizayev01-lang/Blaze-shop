"""
seed.py — Populate database with sample CS2 skins
Run: python seed.py
"""
import asyncio
from models.models import engine, Base, Skin, MarketSource
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SKINS = [
    # ── Rifles ──────────────────────────────────────────────────────────────
    dict(name="AK-47 | Redline", weapon_type="Rifle", exterior="Field-Tested",
         rarity="Classified", float_val=0.2541, price=65000,
         collection="The Phoenix Collection", is_featured=True, stock=3,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHAQFvIWkVMiTneFLWdz-BniibmID4kqbhMmNj0M5T18mPiYqm31e8uxKgqhNpZDz6IoKLMlhp0g/"),
    dict(name="AK-47 | Asiimov", weapon_type="Rifle", exterior="Field-Tested",
         rarity="Covert", float_val=0.3012, price=125000,
         is_featured=True, stock=2,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEptXaakkOKzHhFlbOiB9ji2mI7fQ--Sh8HXxRkG6ZIpiLuRqt3w0VCzqRBlNmj1JI-ScVNqMQ/"),
    dict(name="M4A4 | Howl", weapon_type="Rifle", exterior="Field-Tested",
         rarity="Contraband", float_val=0.2889, price=4500000,
         is_featured=True, stock=1,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaQKMiT3eFLS5D5BvYbngYiEw_b0NLnWmWlWv9Vj3ejDorEh0mq8rBJjYHvzcpOqZFJtMQ/"),
    dict(name="AK-47 | Fire Serpent", weapon_type="Rifle", exterior="Field-Tested",
         rarity="Covert", float_val=0.3456, price=750000, stock=1,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaQKMiTnfW3bwD5BvYbngYiExb2nMrrTxW9Y7ZVpi9Wt2dv0rdLiqhI6Zmqjdo3AcQ4/"),
    dict(name="M4A1-S | Hyper Beast", weapon_type="Rifle", exterior="Factory New",
         rarity="Covert", float_val=0.0312, price=185000, stock=2, is_featured=True,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaQKMiT3eFLS5D5BvYbngYiEw_ShNeHUxj5T75Ih3OuVrdCk21Hi-hFoMj31IqSco1hp0A/"),
    dict(name="FAMAS | Afterimage", weapon_type="Rifle", exterior="Field-Tested",
         rarity="Restricted", float_val=0.2789, price=12000, stock=10),
    dict(name="Galil AR | Chatterbox", weapon_type="Rifle", exterior="Factory New",
         rarity="Classified", float_val=0.0543, price=35000, stock=5),

    # ── Pistols ─────────────────────────────────────────────────────────────
    dict(name="Desert Eagle | Blaze", weapon_type="Pistol", exterior="Factory New",
         rarity="Restricted", float_val=0.0012, price=220000,
         is_featured=True, stock=2,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaYKMiTxfGBhno2OxtODh9fev7-KhKQDrH5Q18ux4tTh98yw2dKz4xVqN2imSoiLdA8/"),
    dict(name="Glock-18 | Fade", weapon_type="Pistol", exterior="Factory New",
         rarity="Classified", float_val=0.0089, price=165000, stock=3),
    dict(name="USP-S | Kill Confirmed", weapon_type="Pistol", exterior="Field-Tested",
         rarity="Covert", float_val=0.2245, price=95000, stock=4, is_featured=True),
    dict(name="P250 | See Ya Later", weapon_type="Pistol", exterior="Factory New",
         rarity="Classified", float_val=0.0321, price=28000, stock=8),
    dict(name="Five-SeveN | Monkey Business", weapon_type="Pistol", exterior="Factory New",
         rarity="Classified", float_val=0.0456, price=18000, stock=6),

    # ── Sniper Rifles ────────────────────────────────────────────────────────
    dict(name="AWP | Dragon Lore", weapon_type="Sniper Rifle", exterior="Field-Tested",
         rarity="Covert", float_val=0.3789, price=8500000,
         is_featured=True, stock=1,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaQKMiT3eFLS5D5BvYbngYiEw_ahNeGXxhRu4ct3i7rG84-h2FK8rkNqNzGnItKQMlho0Q/"),
    dict(name="AWP | Asiimov", weapon_type="Sniper Rifle", exterior="Field-Tested",
         rarity="Covert", float_val=0.2654, price=185000, stock=3, is_featured=True),
    dict(name="AWP | Neon Rider", weapon_type="Sniper Rifle", exterior="Minimal Wear",
         rarity="Covert", float_val=0.1123, price=95000, stock=2),
    dict(name="SSG 08 | Blood in the Water", weapon_type="Sniper Rifle", exterior="Factory New",
         rarity="Classified", float_val=0.0234, price=42000, stock=5),
    dict(name="AWP | Lightning Strike", weapon_type="Sniper Rifle", exterior="Factory New",
         rarity="Classified", float_val=0.0089, price=125000, stock=2),

    # ── Knives ──────────────────────────────────────────────────────────────
    dict(name="Karambit | Fade", weapon_type="Knife", exterior="Factory New",
         rarity="Covert", float_val=0.0045, price=3200000,
         is_featured=True, stock=1,
         image_url="https://community.akamai.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX3oFJZIHbOz3gJlDXXsNAhp7SGBfUpDnhJSKh2tHBEp0XaQKMiTneFLWdz-BniibmID4kqXhMmNj0M5T18mOoOuiNSh24qt2FK8rkNqNzGnItKQMlho0Q/"),
    dict(name="Butterfly Knife | Crimson Web", weapon_type="Knife", exterior="Minimal Wear",
         rarity="Covert", float_val=0.1234, price=2800000, stock=1),
    dict(name="M9 Bayonet | Doppler", weapon_type="Knife", exterior="Factory New",
         rarity="Covert", float_val=0.0056, pattern=412, price=1900000, stock=1),
    dict(name="Karambit | Doppler", weapon_type="Knife", exterior="Factory New",
         rarity="Covert", float_val=0.0034, pattern=166, price=2100000, stock=1),
    dict(name="Flip Knife | Tiger Tooth", weapon_type="Knife", exterior="Factory New",
         rarity="Covert", float_val=0.0023, price=850000, stock=2),
    dict(name="Huntsman Knife | Marble Fade", weapon_type="Knife", exterior="Factory New",
         rarity="Covert", float_val=0.0067, price=680000, stock=2),

    # ── Gloves ──────────────────────────────────────────────────────────────
    dict(name="Sport Gloves | Pandora's Box", weapon_type="Gloves", exterior="Field-Tested",
         rarity="Covert", float_val=0.3456, price=2500000, is_featured=True, stock=1),
    dict(name="Specialist Gloves | Crimson Kimono", weapon_type="Gloves", exterior="Well-Worn",
         rarity="Covert", float_val=0.4321, price=950000, stock=1),
    dict(name="Hand Wraps | Cobalt Skulls", weapon_type="Gloves", exterior="Field-Tested",
         rarity="Covert", float_val=0.2789, price=1200000, stock=1),

    # ── SMGs ────────────────────────────────────────────────────────────────
    dict(name="MP7 | Bloodsport", weapon_type="SMG", exterior="Factory New",
         rarity="Classified", float_val=0.0312, price=28000, stock=8),
    dict(name="UMP-45 | Fade", weapon_type="SMG", exterior="Factory New",
         rarity="Classified", float_val=0.0145, price=22000, stock=6),
    dict(name="P90 | Asiimov", weapon_type="SMG", exterior="Field-Tested",
         rarity="Covert", float_val=0.2345, price=45000, stock=5),

    # ── Shotguns ─────────────────────────────────────────────────────────────
    dict(name="MAG-7 | SWAG-7", weapon_type="Shotgun", exterior="Factory New",
         rarity="Mil-Spec", float_val=0.0678, price=8000, stock=15),
    dict(name="Nova | Hyper Beast", weapon_type="Shotgun", exterior="Field-Tested",
         rarity="Classified", float_val=0.2456, price=14000, stock=10),
]

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if skins already exist
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(Skin))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} skins. Skipping seed.")
            return

        skins = [
            Skin(
                market_source=MarketSource.MANUAL,
                **{k: v for k, v in s.items()}
            )
            for s in SKINS
        ]
        db.add_all(skins)
        await db.commit()
        print(f"✅ Seeded {len(skins)} skins successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
