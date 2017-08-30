import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

class ZergRushBot(sc2.BotAI):
    def __init__(self):
        self.drone_counter = 0
        self.overlord_counter = 0
        self.extractor_started = False
        self.spawning_pool_started = False
        self.moved_workers_to_gas = False
        self.moved_workers_from_gas = False
        self.queeen_started = False

    async def on_step(self, state, iteration):
        if not self.units(HATCHERY).ready.exists:
            for unit in self.workers | self.units(ZERGLING) | self.units(QUEEN):
                await self.do(unit.attack(self.enemy_start_locations[0]))
            return

        hatchery = self.units(HATCHERY).ready.first
        larvae = self.units(LARVA)

        target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
        for zl in self.units(ZERGLING).idle:
            await self.do(zl.attack(target))

        for queen in self.units(QUEEN).idle:
            await self.do(queen(INJECTLARVA, hatchery))

        if self.vespene >= 100:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 100:
                await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))

            if not self.moved_workers_from_gas:
                self.moved_workers_from_gas = True
                for drone in self.workers:
                    m = state.mineral_field.closer_than(10, drone.position)
                    await self.do(drone.gather(m.random, queue=True))

        if self.supply_left < 2:
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))
                return

        if self.units(SPAWNINGPOOL).ready.exists:
            if larvae.exists and self.minerals > self.can_afford(ZERGLING):
                await self.do(larvae.random.train(ZERGLING))
                return

        if self.units(EXTRACTOR).ready.exists and not self.moved_workers_to_gas:
            self.moved_workers_to_gas = True
            extractor = self.units(EXTRACTOR).first
            for drone in self.workers.random_group_of(3):
                await self.do(drone.gather(extractor))

        if self.minerals > 500:
            for d in range(4, 15):
                pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                if await self.can_place(HATCHERY, pos):
                    self.spawning_pool_started = True
                    await self.do(self.workers.random.build(HATCHERY, pos))
                    break

        if self.drone_counter < 3:
            if self.minerals >= self.can_afford(DRONE):
                self.drone_counter += 1
                await self.do(larvae.random.train(DRONE))
                return

        if not self.extractor_started:
            if self.minerals >= self.can_afford(EXTRACTOR):
                drone = self.workers.random
                target = state.vespene_geyser.closest_to(drone.position)
                err = await self.do(drone.build(EXTRACTOR, target))
                if not err:
                    self.extractor_started = True

        elif not self.spawning_pool_started:
            if self.minerals >= self.can_afford(SPAWNINGPOOL):

                for d in range(4, 15):
                    pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                    if await self.can_place(SPAWNINGPOOL, pos):
                        drone = self.workers.closest_to(pos)
                        err = await self.do(drone.build(SPAWNINGPOOL, pos))
                        if not err:
                            self.spawning_pool_started = True
                            break

        elif not self.queeen_started:
            if self.minerals >= self.can_afford(QUEEN):
                r = await self.do(hatchery.train(QUEEN))
                if not r:
                    self.queeen_started = True

def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, ZergRushBot()),
        Computer(Race.Terran, Difficulty.Medium)
    ], realtime=True)

if __name__ == '__main__':
    main()