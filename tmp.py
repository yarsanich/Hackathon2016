new_user = User(login="login", email="email", password="pass_hash", name="Name")
new_user.save()

new_info_block = InfoBlock(title="title", image="path", description="description")
blocks = InfoBlock.select()
new_info_block.save()

registered_user = Registered(name="Name", email="email", message="message")
blocks = Registered.select()
registered_user.save()

menu = Menu(title="title", link="link")
menu.save()
