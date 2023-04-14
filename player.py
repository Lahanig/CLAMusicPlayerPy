import main, asyncio

main.player.base_path_flag = True
run_app = asyncio.ensure_future(main.player.main())
event_loop = asyncio.get_event_loop()
event_loop.run_forever()