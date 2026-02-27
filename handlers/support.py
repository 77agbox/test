@router.message(lambda m: m.text == "❌ Отписаться от рассылки")
async def unsubscribe_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    unsubscribe(user_id)

    await message.answer("❌ Вы отписались от рассылки.")
