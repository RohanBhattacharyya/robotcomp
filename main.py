import robotcomp
import random

def my_bot(api: robotcomp.BotAPI) -> None:
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    else:
        random_direction = random.choice(["forward", "back", "left", "right"])
        if random_direction == "forward":
            api.move_forward()
        elif random_direction == "back":
            api.move_back()
        elif random_direction == "left":
            api.move_left()
        elif random_direction == "right":
            api.move_right()


player = robotcomp.create_bot("Player", my_bot, "P")
robotcomp.play(player, fast=True, seed=42)