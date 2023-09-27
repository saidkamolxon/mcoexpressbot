from aiogram.dispatcher.filters.state import State, StatesGroup


class AllStates(StatesGroup):
    group_name = State()
    asked_trailer = State()
    asked_lane = State()
    asked_truck = State()
    deleted_user = State()
    made_admin = State()
    md_origin = State()
    md_destination = State()
    sql = State()


class ScheduleMessageStates(StatesGroup):
    WaitingForTime = State()
    WaitingForReceivers = State()
    WaitingForMessage = State()
    WaitingForType = State()
    WaitingForSequence = State()
    WaitingForWeekday = State()
