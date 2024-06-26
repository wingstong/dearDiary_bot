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


async def get_user_tasks(session: async_session, user_id: int):
    async with session() as db_session:
        result = await db_session.execute(select(TODO).where(TODO.user_id == user_id))
        return result.scalars().all()

