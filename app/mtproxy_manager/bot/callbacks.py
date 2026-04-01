from aiogram.filters.callback_data import CallbackData


class SubscriptionPlanCallback(CallbackData, prefix="plan"):
    code: str
