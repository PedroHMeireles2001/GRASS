from typing import Callable, Optional



import time

class Combat:
    TURN_DELAY = 1.0  # segundos

    def __init__(self, game, enemies):
        self.game = game
        self.enemies = enemies
        self.turn_order = self._iniciative()
        self.turn_index = 0

        self.running = True
        self.victory = False
        self.is_player_turn = False

        self.last_turn_time = time.time()
        self.log = []

        self.action_queue: list[TimedAction] = []
        self.current_action: TimedAction | None = None

    def print_text(self,text: str,delay: float = 3.0):
        self.action_queue.append(TimedAction(text=text,action=None,delay=delay))

    def delayed_action(self,action:Callable, text:str = None,delay: float = 3.0):
        action = TimedAction(
            delay=delay,
            action=action,
            text=text
        )
        self.action_queue.append(action)

    def _print_text(self, text):
        self.log.append(text)

    def get_participants(self):
        return [self.game.player] + self.enemies

    def get_active_entity(self):
        return self.turn_order[self.turn_index]



    def update(self):
        self._check_end()

        # se tiver ação rodando
        if self.current_action:
            if self.current_action.ready():
                if self.current_action.action:
                    self.current_action.action()
                if self.current_action.text:
                    self.log.append(self.current_action.text)
                self.current_action = None
            return

        # se tiver ações na fila, começa a próxima
        if self.action_queue:
            self.current_action = self.action_queue.pop(0)
            self.current_action.start()
            return

        # se não tem ações, avança turno
        self._process_turn()


    def end_player_turn(self):
        self.is_player_turn = False
        self._next_turn()
        self.last_turn_time = time.time()

    def _check_end(self):
        if not self.running:
            return

        if len(self.get_alives_enemies()) == 0:
            self.running = False
            self.action_queue.append(
                TimedAction(
                    text="Victory!",
                    delay=3.0,
                    action=lambda: self._end(True),
                )
            )

        elif self.game.player.dead:
            self.running = False
            self.action_queue.append(
                TimedAction(
                    text="Defeat!",
                    delay=3.0,
                    action=lambda: self._end(False),
                )
            )

    def _end(self,victory: bool):
        self.action_queue.clear()
        self.victory = victory
        self.running = False
        self.game.chat.submit(f"event:combat_ended\nVictory:{str(self.victory)}\nFlee:{str(False)}")

    def _process_turn(self):
        active = self.get_active_entity()

        # Turno do jogador → espera UI
        if active == self.game.player:
            self.is_player_turn = True
            return

        # Turno do inimigo → chama take_turn UMA vez
        self.is_player_turn = False
        active.take_turn(self)

        # IMPORTANTE: só avança turno quando TODAS ações acabarem
        self._next_turn()

    def _next_turn(self):
        self.turn_index += 1
        if self.turn_index >= len(self.turn_order):
            self.turn_index = 0

    def _iniciative(self):
        participants = self.get_participants()

        # Calcula iniciativa para cada entidade
        rolls = []
        for entity in participants:
            roll = entity.iniciative()
            rolls.append((roll, entity))

        # Ordena do maior para o menor
        rolls.sort(key=lambda x: x[0], reverse=True)

        # Salva apenas as entidades na ordem
        turn_order = [entity for _, entity in rolls]

        return turn_order

    def flee(self):
        pass

    def get_alives_enemies(self):
        return [e for e in self.enemies if not e.dead]


class TimedAction:
    def __init__(self, delay: float, action: Optional[Callable],text:str):
        self.delay = delay
        self.action = action
        self.start_time = None
        self.text = text

    def start(self):
        self.start_time = time.time()

    def ready(self):
        return time.time() - self.start_time >= self.delay