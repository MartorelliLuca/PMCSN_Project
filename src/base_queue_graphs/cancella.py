import os

    def run_finite_horizon(mode: str, scenario: str, out_csv: str, model: str = "baseline"):
        if os.path.exists(out_csv):
            os.remove(out_csv)

        arrival_p = ARRIVAL_P
        arrival_l1 = ARRIVAL_L1_x40
        arrival_l2 = ARRIVAL_L2_x40

        fieldnames = transitory_fieldnames(MAX_SPIKE_NUMBER)
        all_logs = []

        if mode == "transitory":
            for rep in range(REPLICATION_FACTOR_TRANSITORY):
                seed = SEEDS_TRANSITORY[rep % len(SEEDS_TRANSITORY)]
                plantSeeds(seed)

                env = simpy.Environment()
                system = DDoSSystem(env, mode, arrival_p, arrival_l1, arrival_l2, variant=model)

                def checkpointer_optimized(env, system, rep_id):
                    checkpoint_times = []
                    t = CHECKPOINT_TIME_TRANSITORY
                    while t <= STOP_CONDITION_TRANSITORY:
                        checkpoint_times.append(t)
                        t += CHECKPOINT_TIME_TRANSITORY

                    for cp_time in checkpoint_times:
                        yield env.timeout(cp_time - env.now)
                        snap = system.snapshot(env.now, replica_id=rep_id)
                        snap["scenario"] = scenario
                        snap["mode"] = mode
                        snap["is_final"] = (cp_time == checkpoint_times[-1])
                        all_logs.append(snap)
                        append_row_stable(out_csv, snap, fieldnames)
                        progress = (cp_time / STOP_CONDITION_TRANSITORY) * 100
                        print(f"  Replica {rep+1}: {progress:.1f}% completato")

                env.process(checkpointer_optimized(env, system, rep))
                env.run(until=STOP_CONDITION_TRANSITORY)
                print(f"Replica {rep+1} completata!")

        elif mode == "finite simulation":
            seeds = [1234566789]
            for rep in range(REPLICATION_FACTORY_FINITE_SIMULATION):
                plantSeeds(seeds[rep])
                env = simpy.Environment()
                system = DDoSSystem(env, mode, arrival_p, arrival_l1, arrival_l2, variant=model)

                def checkpointer(env, system, rep_id):
                    next_cp = CHECKPOINT_TIME_FINITE_SIMULATION
                    while next_cp <= STOP_CONDITION_FINITE_SIMULATION:
                        yield env.timeout(next_cp - env.now)
                        snap = system.snapshot(env.now, replica_id=rep_id)
                        snap["scenario"] = scenario
                        snap["mode"] = mode
                        snap["is_final"] = False
                        all_logs.append(snap)
                        append_row_stable(out_csv, snap, fieldnames)
                        next_cp += CHECKPOINT_TIME_FINITE_SIMULATION

                    if env.now < STOP_CONDITION_FINITE_SIMULATION:
                        yield env.timeout(STOP_CONDITION_FINITE_SIMULATION - env.now)
                        snap = system.snapshot(env.now, replica_id=rep_id)
                        snap["scenario"] = scenario
                        snap["mode"] = mode
                        snap["is_final"] = True
                        all_logs.append(snap)
                        append_row_stable(out_csv, snap, fieldnames)

                env.process(checkpointer(env, system, rep))
                env.run(until=STOP_CONDITION_FINITE_SIMULATION)

                selectStream(RNG_STREAM)
                seeds.append(getSeed())

        return all_logs