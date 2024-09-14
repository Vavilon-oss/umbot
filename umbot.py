from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from datetime import datetime

# Определение состояний
CHOOSING_TRAINING_TYPE, CHOOSING_EXERCISES, CHOOSING_MUSCLE, CHOOSING_EXERCISE, CHOOSING_WEIGHT, CHOOSING_SETS, CHOOSING_REPS, CHOOSING_LEVEL, CHOOSING_TIME = range(9)

exercises = {
    'Силовые тренировки': {
        'Грудь': ['Жим штанги лежа', 'Жим гантелей на наклонной скамье', 'Разводка гантелей', 'Грудь бабочка', 'Отжимания на брусьях'],
        'Трицепсы': ['Отжимания на брусьях', 'Французский жим', 'Жим узким хватом'],
        'Спина': ['Тяга верхнего блока к груди', 'Тяга горизонтального блока', 'Подтягивания'],
        'Бицепсы': ['Сгибание рук с гантелями стоя', 'Сгибание рук на скамье Скотта', 'Подтягивания'],
        'Ноги': ['Жим ногами', 'Разгибание ног сидя', 'Сгибание ног лежа'],
        'Плечи': ['Подъем рук в стороны', 'Жим гантелей сидя', 'Разводка гантелей в стороны'],
        'Кардио': ['Эллиптический тренажер', 'Беговая дорожка', 'Велотренажер'],
        'Корпус': ['Скручивания', 'Подъем ног в висе', 'Планка'],
        'Руки': ['Сгибание рук на бицепс в кроссовере', 'Французский жим лежа', 'Молотковые сгибания']
    },
    'Тренировки с собственным весом': {
        'Грудь': ['Отжимания', 'Отжимания на одной руке', 'Отжимания с узким хватом'],
        'Трицепсы': ['Отжимания на брусьях', 'Отжимания на одной руке'],
        'Спина': ['Подтягивания', 'Подтягивания с узким хватом', 'Подтягивания с широкой постановкой рук'],
        'Бицепсы': ['Подтягивания обратным хватом', 'Подтягивания с широкой постановкой рук'],
        'Ноги': ['Приседания', 'Выпады', 'Шагающие выпады'],
        'Плечи': ['Отжимания с узким хватом', 'Подъемы рук в стороны'],
        'Корпус': ['Планка', 'Скручивания', 'Подъем ног в висе']
    },
    'Кардио тренировки': {
        'Кардио': ['Бег на улице', 'Беговая дорожка', 'Велотренажер', 'Эллиптический тренажер']
    }
}

async def delete_my_commands(update: Update, context: CallbackContext) -> None:
    try:
        await context.bot.delete_my_commands()
    except Exception as e:
        print(f"Ошибка при удалении команд: {e}")

async def start(update: Update, context: CallbackContext) -> int:
    message_id = update.message.message_id
    context.user_data['messages_to_delete'] = [message_id]
    
    keyboard = [[InlineKeyboardButton("Записать тренировку", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await update.message.reply_text('Привет! Нажми кнопку ниже, чтобы записать тренировку.', reply_markup=reply_markup)
    context.user_data['messages_to_delete'].append(message.message_id)
    
    await delete_my_commands(update, context)
    
    return ConversationHandler.END

async def start_training(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if 'commands_deleted' not in context.user_data.get(user_id, {}):
        await delete_my_commands(update, context)
        context.user_data[user_id] = {'commands_deleted': True}

    context.user_data[user_id]['exercises'] = []
    context.user_data[user_id]['messages_to_delete'] = []
    context.user_data[user_id]['selected_muscles'] = set()

    keyboard = [[InlineKeyboardButton('Силовые тренировки', callback_data='strength')],
                [InlineKeyboardButton('Тренировки с собственным весом', callback_data='bodyweight')],
                [InlineKeyboardButton('Кардио тренировки', callback_data='cardio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await query.edit_message_text(text="Выберите тип тренировки:", reply_markup=reply_markup)
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    
    return CHOOSING_TRAINING_TYPE

async def choose_training_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    training_type = query.data
    user_id = query.from_user.id

    if training_type == 'strength':
        context.user_data[user_id]['training_type'] = 'Силовые тренировки'
    elif training_type == 'bodyweight':
        context.user_data[user_id]['training_type'] = 'Тренировки с собственным весом'
    elif training_type == 'cardio':
        context.user_data[user_id]['training_type'] = 'Кардио тренировки'
    else:
        await query.edit_message_text('Некорректный тип тренировки.')
        return CHOOSING_TRAINING_TYPE

    message = await query.edit_message_text(text="Введите количество упражнений для тренировки:")
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    
    return CHOOSING_EXERCISES

async def delete_previous_messages(context: CallbackContext, user_id: int) -> None:
    for message_id in context.user_data.get(user_id, {}).get('messages_to_delete', []):
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
    context.user_data[user_id]['messages_to_delete'] = []

async def choose_exercises(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)
    
    try:
        num_exercises = int(update.message.text)
        context.user_data[user_id]['num_exercises'] = num_exercises
        context.user_data[user_id]['current_exercise'] = 0

        return await ask_muscle_group(update, context)
    except ValueError:
        message = await update.message.reply_text('Пожалуйста, введите число.')
        context.user_data[user_id]['messages_to_delete'].append(message.message_id)
        return CHOOSING_EXERCISES

async def ask_muscle_group(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    training_type = context.user_data[user_id].get('training_type')

    if not training_type:
        return CHOOSING_TRAINING_TYPE

    muscle_keyboard = [[InlineKeyboardButton(muscle, callback_data=muscle)] for muscle in exercises[training_type].keys()]
    reply_markup = InlineKeyboardMarkup(muscle_keyboard)
    message = await update.message.reply_text('Выберите мышечную группу для следующего упражнения:', reply_markup=reply_markup)
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    return CHOOSING_MUSCLE

async def choose_muscle(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    muscle = query.data
    user_id = query.from_user.id

    context.user_data[user_id]['current_muscle'] = muscle

    training_type = context.user_data[user_id].get('training_type')
    exercises_list = exercises[training_type].get(muscle, [])
    exercise_keyboard = [[InlineKeyboardButton(ex, callback_data=ex)] for ex in exercises_list]
    reply_markup = InlineKeyboardMarkup(exercise_keyboard)
    message = await query.edit_message_text('Выберите упражнение:', reply_markup=reply_markup)
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    return CHOOSING_EXERCISE

async def choose_exercise(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    exercise = query.data
    user_id = query.from_user.id

    context.user_data[user_id]['current_exercise'] = exercise
    training_type = context.user_data[user_id].get('training_type')

    if training_type == 'Кардио тренировки':
        message = await query.edit_message_text(f"Введите уровень для упражнения '{exercise}':")
        context.user_data[user_id]['messages_to_delete'].append(message.message_id)
        return CHOOSING_LEVEL
    else:
        message = await query.edit_message_text(f"Введите вес для упражнения '{exercise}':")
        context.user_data[user_id]['messages_to_delete'].append(message.message_id)
        return CHOOSING_WEIGHT

async def set_weight(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)

    weight = update.message.text
    context.user_data[user_id]['current_weight'] = weight
    message = await update.message.reply_text(f"Введите количество подходов для упражнения '{context.user_data[user_id]['current_exercise']}' с весом {weight} кг:")
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    return CHOOSING_SETS

async def set_sets(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)

    sets = update.message.text
    context.user_data[user_id]['current_sets'] = sets
    message = await update.message.reply_text(f"Введите количество повторений для упражнения с {sets} подходами:")
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    return CHOOSING_REPS

async def set_reps(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)

    reps = update.message.text
    exercise = context.user_data[user_id]['current_exercise']
    weight = context.user_data[user_id]['current_weight']
    sets = context.user_data[user_id]['current_sets']
    muscle = context.user_data[user_id]['current_muscle']
    training_type = context.user_data[user_id].get('training_type')

    if 'exercises' not in context.user_data[user_id]:
        context.user_data[user_id]['exercises'] = []
    context.user_data[user_id]['exercises'].append({
        'training_type': training_type,
        'muscle': muscle,
        'exercise': exercise,
        'sets': sets,
        'reps': reps,
        'weight': weight
    })

    num_exercises = context.user_data[user_id].get('num_exercises', 0)
    if len(context.user_data[user_id]['exercises']) < num_exercises:
        return await ask_muscle_group(update, context)
    else:
        await delete_previous_messages(context, user_id)

        current_date = datetime.now().strftime('%d.%m.%Y')

        result = f"*Запись тренировки: {current_date}*\n"
        result += f"*Тип тренировки:* {training_type}\n"
        result += f"*Выбранные мышечные группы:* {', '.join(context.user_data[user_id]['selected_muscles'])}\n\n"
        
        for ex in context.user_data[user_id]['exercises']:
            result += f"• *{ex['exercise']}* (Мышцы: {ex['muscle']}):\n"
            result += f"  _{ex['sets']} подходов по {ex['reps']} повторений, вес: {ex['weight']} кг_\n\n"

        await update.message.reply_text(result, parse_mode='Markdown')

        keyboard = [[InlineKeyboardButton("Записать тренировку", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Привет! Нажми кнопку ниже, чтобы записать тренировку.', reply_markup=reply_markup)

        return ConversationHandler.END

async def set_level(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)

    level = update.message.text
    context.user_data[user_id]['current_level'] = level
    message = await update.message.reply_text(f"Введите время для упражнения '{context.user_data[user_id]['current_exercise']}' (в минутах):")
    context.user_data[user_id]['messages_to_delete'].append(message.message_id)
    return CHOOSING_TIME

async def set_time(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    context.user_data[user_id]['messages_to_delete'].append(message_id)

    time = update.message.text
    exercise = context.user_data[user_id]['current_exercise']
    level = context.user_data[user_id]['current_level']
    training_type = context.user_data[user_id].get('training_type')

    if 'exercises' not in context.user_data[user_id]:
        context.user_data[user_id]['exercises'] = []
    context.user_data[user_id]['exercises'].append({
        'training_type': training_type,
        'exercise': exercise,
        'level': level,
        'time': time
    })

    num_exercises = context.user_data[user_id].get('num_exercises', 0)
    if len(context.user_data[user_id]['exercises']) < num_exercises:
        return await ask_muscle_group(update, context)
    else:
        await delete_previous_messages(context, user_id)

        current_date = datetime.now().strftime('%d.%m.%Y')

        result = f"*Запись тренировки: {current_date}*\n"
        result += f"*Тип тренировки:* {training_type}\n"
        
        for ex in context.user_data[user_id]['exercises']:
            if training_type == 'Кардио тренировки':
                result += f"• *{ex['exercise']}* (Уровень: {ex['level']}):\n"
                result += f"  _Время: {ex['time']} мин_\n\n"
            else:
                result += f"• *{ex['exercise']}* (Мышцы: {ex.get('muscle', '')}):\n"
                result += f"  _{ex.get('sets', 'N/A')} подходов по {ex.get('reps', 'N/A')} повторений, вес: {ex.get('weight', 'N/A')} кг_\n\n"

        await update.message.reply_text(result, parse_mode='Markdown')

        keyboard = [[InlineKeyboardButton("Записать тренировку", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Привет! Нажми кнопку ниже, чтобы записать тренировку.', reply_markup=reply_markup)

        return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("7140457169:AAEPtxxaL5WEvSx_rvJUVQwPdWp0wNsk1v4").build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_training, pattern='^start$')],
        states={
            CHOOSING_TRAINING_TYPE: [CallbackQueryHandler(choose_training_type)],
            CHOOSING_EXERCISES: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_exercises)],
            CHOOSING_MUSCLE: [CallbackQueryHandler(choose_muscle)],
            CHOOSING_EXERCISE: [CallbackQueryHandler(choose_exercise)],
            CHOOSING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_weight)],
            CHOOSING_SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_sets)],
            CHOOSING_REPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reps)],
            CHOOSING_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_level)],
            CHOOSING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, start))

    application.run_polling()

if __name__ == '__main__':
    main()
