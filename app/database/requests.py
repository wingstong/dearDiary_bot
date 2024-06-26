from app.database.models import async_session
from app.database.models import User, TODO, DiaryEntry, ReadingList, MoodJournal
from sqlalchemy import select


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()
        return user


async def get_tasks():
    async with async_session() as session:
        return await session.scalars(select(TODO))
