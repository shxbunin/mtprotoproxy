from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from mtproxy_manager.bot.callbacks import SubscriptionPlanCallback
from mtproxy_manager.shared.plans import PLANS


def build_subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=plan.title,
                    callback_data=SubscriptionPlanCallback(code=plan.code).pack(),
                )
            ]
            for plan in PLANS.values()
        ]
    )


def build_connect_keyboard(proxy_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Подключить", url=proxy_link, style="success")
        ]]
    )


def build_admin_keyboard(stats_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть статистику", url=stats_url)]]
    )
