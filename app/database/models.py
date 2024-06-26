from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, Text, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    Id_user: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger)

    todos = relationship("TODO", back_populates="user")
    diary_entries = relationship("DiaryEntry", back_populates="user")
    mood_journals = relationship("MoodJournal", back_populates="user")
    reading_list = relationship("ReadingList", back_populates="user")


class TODO(Base):
    __tablename__ = 'tasklist'

    Id_task: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.Id_user'))
    taskText: Mapped[str] = mapped_column(Text)
    deadLine: Mapped[str] = mapped_column(String(50))
    isComplete: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="todos")


class DiaryEntry(Base):
    __tablename__ = 'diaryentries'

    id_entry: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.Id_user'))
    EntryDate: Mapped[str] = mapped_column(String(50))
    Content: Mapped[str] = mapped_column(Text)

    user = relationship("User", back_populates="diary_entries")


class MoodJournal(Base):
    __tablename__ = 'moodjournal'

    id_mood: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.Id_user'))
    entry_date: Mapped[str] = mapped_column(String(50))
    mood: Mapped[str] = mapped_column(String(50))

    user = relationship("User", back_populates="mood_journals")


class ReadingList(Base):
    __tablename__ = 'readinglist'

    Id_book: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.Id_user'))
    namebook: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(100))
    descriptBook: Mapped[str] = mapped_column(Text)
    isWatched: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="reading_list")

    # To create the tables


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
