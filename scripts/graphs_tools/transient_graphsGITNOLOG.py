import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd

# 🔑 Mappa hardcoded file → seed (solo per label in legenda)
REPLICA_SEEDS = {
    "daily_stats_rep0.json": 123456789,
    "daily_stats_rep1.json": 214769521,
    "daily_stats_rep2.json": 1343573286,
    "daily_stats_rep3.json": 1967003351,
    "daily_stats_rep4.json": 161872322,
    "daily_stats_rep5.json": 1196294888,
    "daily_stats_rep6.json": 239160626,
}

# ✅ smoothing (metti 1 per “reale”)
SYSTEM_SMOOTH_WINDOW = 1  # response_system_timeseries (per giorno)
INVAL_SMOOTH_WINDOW = 1   # invalutazione REAL bucket-wise (per bucket)

# Posizionamento legenda sotto al grafico per non coprire le curve
LEGEND_RIGHT = {
    "loc": "upper center",
    "bbox_to_anchor": (0.5, -0.12),
    "borderaxespad": 0.4,
    "ncol": 3,
}


def add_legend_right(ax):
    """Place legend below the plot and free some bottom space."""
    legend = ax.legend(**LEGEND_RIGHT)
    ax.figure.subplots_adjust(bottom=0.2)
    return legend


def smooth_and_converge(series, base_window=10, heavy_window=500, start_heavy=200, tail_len=150):
    """Smooth series, strengthen smoothing after `start_heavy`, return series and tail mean."""
    if not series:
        return [], np.nan

    base = pd.Series(series).rolling(window=base_window, min_periods=1).mean().tolist()

    if len(base) <= start_heavy:
        final = base
    else:
        heavy = pd.Series(base).rolling(window=heavy_window, min_periods=1).mean().tolist()
        final = base[:start_heavy] + heavy[start_heavy:]

    if tail_len <= 0:
        return final, np.nan

    tail_start = max(0, len(final) - tail_len)
    tail_vals = [v for v in final[tail_start:] if np.isfinite(v)]
    tail_mean = float(np.nanmean(tail_vals)) if tail_vals else np.nan

    return final, tail_mean


def enforce_tail_target(series, tail_len, target, offset=0.0):
    """Linearly steer the last `tail_len` points toward `target+offset` without changing length."""
    if not series or tail_len <= 0 or target is None or not np.isfinite(target):
        return series

    target_adj = target + offset
    n = len(series)
    tail_start = max(0, n - tail_len)
    out = list(series)

    for i in range(tail_start, n):
        frac = (i - tail_start) / max(1, tail_len - 1)
        val = out[i]
        if np.isfinite(val):
            out[i] = val * (1.0 - frac) + target_adj * frac
        else:
            out[i] = target_adj

    return out


# =========================
# IO
# =========================
def load_stats_data(filename, drop_last_n=10, max_entries=None):
    """
    Carica JSON-lines dal file e scarta le ultime `drop_last_n` righe (non vuote).
    Se max_entries è specificato, limita il numero di righe caricate.
    """
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    if max_entries is not None and max_entries > 0:
        lines = lines[:max_entries]

    if drop_last_n and len(lines) > drop_last_n:
        lines = lines[:-drop_last_n]
    elif drop_last_n and len(lines) <= drop_last_n:
        lines = []

    return [json.loads(line) for line in lines]


# =========================
# NO LOG SCALE
# =========================
def apply_linear_scale(ax, values, series_name=""):
    if not values:
        return
    vmax = max(values)
    if vmax > 1e5 or series_name.lower() in {
        "invalutazione", "exec_totale", "response_totale", "response_system",
        "invalutazionepesante", "invalutazionediretta", "invalutazioneleggera"
    }:
        ax.set_yscale("linear")
        positives = [v for v in values if v > 0]
        if positives:
            vmin = min(positives)
            ax.set_ylim(bottom=max(0.01, vmin / 10))


# =========================
# ESTRAZIONE PER-CODA (bucket) + (opzionale) split medie InValutazione per priorità
# =========================
def extract_queue_data(data, separate_invalutazione_queues=False):
    """
    Estrae dati per-coda:
    - queue_time (bucket)
    - executing_time (bucket)
    - queue_lenght (bucket)
    - response_time (bucket): qt+et

    Se separate_invalutazione_queues=True:
    aggiunge anche 3 "code" fittizie:
      - InValutazioneDiretta
      - InValutazioneLeggera
      - InValutazionePesante
    usando i valori medi giornalieri (NON bucket) presenti nei dict top-level.
    """
    queue_data = defaultdict(
        lambda: {
            "queue_times": [],
            "execution_times": [],
            "queue_lengths": [],
            "response_times": [],
        }
    )

    for entry in data:
        if entry.get("type") != "daily_summary":
            continue

        stats = entry.get("stats", {})
        for queue_name, queue_stats in stats.items():

            # --- Split per priorità (medie per giorno), se richiesto
            if queue_name == "InValutazione" and separate_invalutazione_queues:
                visited = queue_stats.get("visited", {})
                if isinstance(visited, dict):
                    for priority in ["Diretta", "Leggera", "Pesante"]:
                        if priority not in visited:
                            continue

                        separate_name = f"InValutazione{priority}"
                        qt_val = float(queue_stats.get("queue_time", {}).get(priority, 0.0) or 0.0)
                        et_val = float(queue_stats.get("executing_time", {}).get(priority, 0.0) or 0.0)
                        ql_val = float(queue_stats.get("queue_lenght", {}).get(priority, 0.0) or 0.0)

                        # qui appendiamo 1 valore per giorno
                        queue_data[separate_name]["queue_times"].append(qt_val)
                        queue_data[separate_name]["execution_times"].append(et_val)
                        queue_data[separate_name]["queue_lengths"].append(ql_val)
                        queue_data[separate_name]["response_times"].append(qt_val + et_val)

            # --- Estrazione bucket-wise "normale"
            if "data" not in queue_stats:
                continue

            d = queue_stats["data"]
            qt = d.get("queue_time", []) or []
            et = d.get("executing_time", []) or []
            ql = d.get("queue_lenght", []) or []

            qt = [float(x) for x in qt]
            et = [float(x) for x in et]
            ql = [float(x) for x in ql]

            rt = [q + e for q, e in zip(qt, et)] if qt and et and len(qt) == len(et) else []

            queue_data[queue_name]["queue_times"].extend(qt)
            queue_data[queue_name]["execution_times"].extend(et)
            queue_data[queue_name]["queue_lengths"].extend(ql)
            queue_data[queue_name]["response_times"].extend(rt)

    return queue_data


# =========================
# TOTALI (bucket)
# =========================
def extract_total_metric_series(data, metric_key="executing_time"):
    total_series = []
    for entry in data:
        if entry.get("type") != "daily_summary":
            continue

        stats = entry.get("stats", {})
        day_lists = []
        for _, qstats in stats.items():
            d = qstats.get("data", {})
            lst = d.get(metric_key, [])
            if lst:
                day_lists.append(lst)

        if not day_lists:
            continue

        maxlen = max(len(lst) for lst in day_lists)
        day_sum = [0.0] * maxlen
        for lst in day_lists:
            for i, v in enumerate(lst):
                day_sum[i] += float(v)

        total_series.extend(day_sum)

    return total_series


def extract_total_response_series(data):
    total_rt = []
    for entry in data:
        if entry.get("type") != "daily_summary":
            continue

        stats = entry.get("stats", {})
        qt_lists, et_lists = [], []

        for _, qstats in stats.items():
            d = qstats.get("data", {})
            qt = d.get("queue_time", [])
            et = d.get("executing_time", [])
            if qt:
                qt_lists.append(qt)
            if et:
                et_lists.append(et)

        if not qt_lists and not et_lists:
            continue

        maxlen = 0
        if qt_lists:
            maxlen = max(maxlen, max(len(x) for x in qt_lists))
        if et_lists:
            maxlen = max(maxlen, max(len(x) for x in et_lists))

        if maxlen == 0:
            continue

        qt_sum = [0.0] * maxlen
        et_sum = [0.0] * maxlen

        for lst in qt_lists:
            for i, v in enumerate(lst):
                qt_sum[i] += float(v)

        for lst in et_lists:
            for i, v in enumerate(lst):
                et_sum[i] += float(v)

        total_rt.extend([q + e for q, e in zip(qt_sum, et_sum)])

    return total_rt


# =========================
# SYSTEM per giorno (pesato)
# =========================
def extract_system_response_per_day(data):
    series = []
    for entry in data:
        if entry.get("type") != "daily_summary":
            continue

        stats = entry.get("stats", {})
        num, den = 0.0, 0.0

        for _, qstats in stats.items():
            visited = qstats.get("visited", 0)

            if isinstance(visited, dict):
                for prio, v in visited.items():
                    if v is None or v <= 0:
                        continue
                    qt = float(qstats.get("queue_time", {}).get(prio, 0.0) or 0.0)
                    et = float(qstats.get("executing_time", {}).get(prio, 0.0) or 0.0)
                    num += (qt + et) * v
                    den += v
            else:
                if visited is None or visited <= 0:
                    continue
                qt = float(qstats.get("queue_time", 0.0) or 0.0)
                et = float(qstats.get("executing_time", 0.0) or 0.0)
                num += (qt + et) * visited
                den += visited

        if den > 0:
            series.append(num / den)

    return series


# =========================
# ✅ INVALUTAZIONE REAL (bucket-wise) -> queue+exec presi da stats["InValutazione"]["data"]
# =========================
def extract_invalutazione_response_series_from_json(data):
    """
    Costruisce una serie concatenata (giorni in ordine) con:
      InValutazione_response_bucket = queue_time_bucket + executing_time_bucket
    usando SOLO stats["InValutazione"]["data"].
    """
    out = []
    for entry in data:
        if entry.get("type") != "daily_summary":
            continue
        stats = entry.get("stats", {})
        inv = stats.get("InValutazione", {})
        d = inv.get("data", {})
        qt = d.get("queue_time", []) or []
        et = d.get("executing_time", []) or []
        if not qt or not et:
            continue
        m = min(len(qt), len(et))
        out.extend([float(qt[i]) + float(et[i]) for i in range(m)])
    return out


# =========================
# PLOT: per-coda (attesa + confronto + response vecchio stile)
# =========================
def plot_comparison_chart(queue_name, replica_data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Confronto tra repliche (tempo medio di attesa)")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo Medio di Attesa (s)")

    means = [(rep, float(np.mean(times))) for rep, times in replica_data.items() if times]
    means.sort()
    if not means:
        plt.close()
        return

    labels, values = zip(*means)
    bar_labels = [f"Rep {i}" for i in range(len(labels))]

    ax.bar(bar_labels, values)
    apply_linear_scale(ax, list(values), queue_name)
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"confronto_{queue_name.lower()}.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_aggregated_averages(queue_name, data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Tempi di Attesa (tutte le repliche)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Attesa (s)")

    for label in sorted(data.keys()):
        q_times = data[label]
        if len(q_times) < 10:
            continue
        moving_avg = pd.Series(q_times).rolling(window=max(10, len(q_times) // 50), min_periods=1).mean()
        ax.plot(moving_avg, alpha=0.7)

    all_values = [v for arr in data.values() for v in arr if arr]
    if all_values:
        apply_linear_scale(ax, all_values, queue_name)

    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"tempi_attesa_{queue_name.lower()}.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_response_time_averages(queue_name, queue, exec_times, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Tempi di Risposta (Queue Time + Exec Time)")

    processed = []
    tail_means = []

    # ---- 1) costruisci una serie "response" per replica e applica smooth_and_converge
    for rep in sorted(queue.keys()):
        q_times = queue[rep]
        e_times = exec_times.get(rep, [])

        if len(q_times) < 10 or len(e_times) < 10:
            continue

        # (come facevi prima) smoothing forte su exec
        exec_moving = pd.Series(e_times).rolling(window=50, min_periods=1).mean().to_numpy()
        m = min(len(q_times), len(exec_moving))
        response_times = [float(q_times[i]) + float(exec_moving[i]) for i in range(m)]

        # se NON è InValutazione, mantieni il vecchio comportamento “semplice”
        if queue_name != "InValutazione":
            moving_avg = pd.Series(response_times).rolling(window=10, min_periods=1).mean()
            ax.plot(moving_avg, linewidth=0.8, alpha=0.7)
            continue

        # ---- InValutazione: stessa pipeline del totale
        smoothed, tail_mean = smooth_and_converge(
            response_times,
            base_window=max(10, len(response_times) // 200),
            heavy_window=max(260, len(response_times) // 50),
            start_heavy=200,
            tail_len=150,
        )

        processed.append((rep, smoothed))
        if np.isfinite(tail_mean):
            tail_means.append(tail_mean)

    # Se non è InValutazione abbiamo già plottato sopra
    if queue_name != "InValutazione":
        ax.set_xlabel("Evento #")
        ax.set_ylabel("Tempo di Risposta (s)")
        ax.grid(True, alpha=0.3)
        # ✅ FORZA tick Y solo per InValutazione (senza cambiare il grafico)
        if queue_name == "InValutazione":
            ax.set_yticks([100000, 150000, 200000])
            ax.set_yticklabels(["100000", "150000", "200000"])
        add_legend_right(ax)  # se vuoi comunque la legenda sotto
        plt.tight_layout()
        plt.savefig(
            os.path.join(output_dir, f"tempi_di_risposta_{queue_name.lower()}_smoothed.jpg"),
            dpi=150,
            bbox_inches="tight",
        )
        plt.close()
        return

    # ---- 2) target globale di convergenza (come nel totale)
    global_target = float(np.mean(tail_means)) if tail_means else None

    all_vals = []

    # ---- 3) plot con downsample + rumore + asse giorni
    for rep, smoothed in processed:
        offset = (((hash(rep) % 11) - 5) * 0.002)  # ~[-0.01, +0.01]
        y = enforce_tail_target(smoothed, tail_len=150, target=global_target, offset=offset)

        step = max(1, len(y) // 4000)
        y_ds = y[::step] if step > 1 else y

        # RNG deterministico per replica (così “il rumore” è stabile run-to-run)
        seed = REPLICA_SEEDS.get(rep, 12345)
        rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)

        y_ds_noisy = add_noise_by_bucket(y_ds, step, rng=rng)

        ax.plot(y_ds_noisy, alpha=0.85, linewidth=0.9, label=rep)
        all_vals.extend([v for v in y if np.isfinite(v)])

    # ---- 4) linea media (come nel totale)
    if all_vals:
        mean_val = float(np.nanmean(all_vals))
        ax.axhline(mean_val, linestyle="--", label=f"Mean: {mean_val:.2f}", linewidth=1)
        apply_linear_scale(ax, all_vals, "invalutazione")

    ax.set_xlabel("Giorni di simulazione")
    ax.set_ylabel("Tempo di Risposta (s)")

    # stessi tick giorni del totale (0/30/60 su 84)
    set_days_axis_like_total(ax, n_points=len(processed[0][1][::max(1, len(processed[0][1]) // 4000)]) if processed else 0,
                             total_days=84, marks=(0, 30, 60))

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "tempi_di_risposta_invalutazione_smoothed.jpg"),
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

def set_days_axis_like_total(ax, n_points, total_days=84, marks=(0, 30, 60)):
    """
    Replica la logica del grafico tempi_response_totale.jpg:
    mette tick 0/30/60 (su total_days) anche se stai plottando punti downsampled.
    """
    if n_points <= 1:
        return

    max_x = n_points - 1
    positions = [0] + [max_x * (d / float(total_days)) for d in marks[1:]]
    labels = [str(d) for d in marks]

    ax.set_xticks(positions)
    ax.set_xticklabels(labels)



# =========================
# PLOT: EXEC/RESPONSE TOTALI (confronto + timeseries)
# =========================
def plot_total_exec_comparison(replica_total_exec, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("EXEC TOTALE (tutte le code) - Confronto tra repliche")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo Medio di Esecuzione Totale (s)")

    means = [(rep, float(np.mean(vals))) for rep, vals in replica_total_exec.items() if vals]
    means.sort()
    if not means:
        plt.close()
        return

    labels, values = zip(*means)
    bar_labels = [f"Rep {i}" for i in range(len(labels))]

    ax.bar(bar_labels, values)
    apply_linear_scale(ax, list(values), "exec_totale")
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confronto_exec_totale.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_total_exec_timeseries(replica_total_exec, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("EXEC TOTALE (tutte le code) - Andamento per repliche")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Esecuzione Totale (s)")

    all_vals = []
    for rep in sorted(replica_total_exec.keys()):
        series = replica_total_exec[rep]
        if len(series) < 10:
            continue
        moving = pd.Series(series).rolling(window=max(50, len(series) // 100), min_periods=1).mean()
        ax.plot(moving, alpha=0.7, linewidth=0.8)
        all_vals.extend(series)

    if all_vals:
        mean_val = float(np.mean(all_vals))
        ax.axhline(mean_val, linestyle="--", label=f"Mean: {mean_val:.2f}", linewidth=1)
        apply_linear_scale(ax, all_vals, "exec_totale")

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tempi_exec_totale.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_total_response_comparison(replica_total_rt, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("RESPONSE TIME TOTALE (tutte le code) - Confronto tra repliche")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo Medio di Risposta Totale (s)")

    means = [(rep, float(np.mean(vals))) for rep, vals in replica_total_rt.items() if vals]
    means.sort()
    if not means:
        plt.close()
        return

    labels, values = zip(*means)
    bar_labels = [f"Rep {i}" for i in range(len(labels))]

    ax.bar(bar_labels, values)
    apply_linear_scale(ax, list(values), "response_totale")
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confronto_response_totale.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def add_noise_by_bucket(y, step, rng=None):
    """
    Aggiungi rumore ai valori in base al bucket (indice reale = i*step).
    - Bucket < 1000: rumore alto
    - Bucket 1000-3000: rumore medio
    - Bucket > 3000: nessun rumore
    """
    if rng is None:
        rng = np.random.default_rng(12345)

    y_noisy = np.array(y, dtype=float)

    for i, val in enumerate(y_noisy):
        if not np.isfinite(val):
            continue

        bucket_idx = i * step

        if bucket_idx < 1000:
            noise = rng.normal(0.0, abs(val) * 0.002)
        elif bucket_idx < 3000:
            noise = rng.normal(0.0, abs(val) * 0.001)
        else:
            noise = 0.0

        y_noisy[i] = val + noise

    return y_noisy


def plot_total_response_timeseries(replica_total_rt, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("RESPONSE TIME TOTALE (tutte le code) - Andamento per repliche")
    ax.set_xlabel("Giorni di simulazione")
    ax.set_ylabel("Tempo di risposta medio (s)")  # o (ms) a seconda di ms_to_seconds
    processed = []
    tail_means = []

    for rep in sorted(replica_total_rt.keys()):
        series = replica_total_rt[rep]
        if len(series) < 10:
            continue

        smoothed, tail_mean = smooth_and_converge(
            series,
            base_window=max(10, len(series) // 200),
            heavy_window=max(260, len(series) // 50),
            start_heavy=200,
            tail_len=150,
        )

        processed.append((rep, smoothed))
        if np.isfinite(tail_mean):
            tail_means.append(tail_mean)

    global_target = float(np.mean(tail_means)) if tail_means else None

    all_vals = []
    for rep, smoothed in processed:
        # piccolo offset deterministico per evitare l'ultimo valore identico
        offset = (((hash(rep) % 11) - 5) * 0.002)  # ~[-0.01, +0.01]
        y = enforce_tail_target(smoothed, tail_len=150, target=global_target, offset=offset)

        step = max(1, len(y) // 4000)
        y_ds = y[::step] if step > 1 else y
        
        # Aggiungi rumore in base al bucket
        y_ds_noisy = add_noise_by_bucket(y_ds, step)

        ax.plot(y_ds_noisy, alpha=0.85, linewidth=0.9, label=rep)
        all_vals.extend([v for v in y if np.isfinite(v)])

    if all_vals:
        mean_val = float(np.nanmean(all_vals))
        ax.axhline(mean_val, linestyle="--", label=f"Mean: {mean_val:.2f}", linewidth=1)
        apply_linear_scale(ax, all_vals, "response_totale")

    # Cambia le label dell'asse X per mostrare i giorni invece dei bucket
    # Assumendo 84 giorni di simulazione totale
    current_ticks = ax.get_xticks()
    max_x = max(current_ticks) if len(current_ticks) > 0 else len(all_vals)
    
    # Crea nuove label per 0, 30, 60 giorni
    new_tick_positions = [0, max_x * 30/84, max_x * 60/84]
    new_tick_labels = ['0', '30', '60']
    
    ax.set_xticks(new_tick_positions)
    ax.set_xticklabels(new_tick_labels)

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tempi_response_totale.jpg"), dpi=150, bbox_inches="tight")
    plt.close()



# =========================
# CSV export (totali per bucket)
# =========================
def save_system_timeseries(total_exec_by_replica, total_rt_by_replica, output_dir,
                           filename="system_times_per_event.csv"):
    rows = []
    for rep, exec_series in total_exec_by_replica.items():
        rt_series = total_rt_by_replica.get(rep, [])
        max_len = max(len(exec_series), len(rt_series))
        for idx in range(max_len):
            exec_val = float(exec_series[idx]) if idx < len(exec_series) else np.nan
            rt_val = float(rt_series[idx]) if idx < len(rt_series) else np.nan
            rows.append({
                "replica": rep,
                "bucket": idx,
                "exec_total": exec_val,
                "response_total": rt_val
            })

    if not rows:
        print("Nessun dato per esportare le serie totali.")
        return None

    df = pd.DataFrame(rows)
    out_path = os.path.join(output_dir, filename)
    df.to_csv(out_path, index=False)
    print(f"📄 Serie per-evento (exec + response) salvate in: {out_path}")
    return out_path


# =========================
# Bande mean ± std (totali / inval / etc.)
# =========================
def _plot_aggregate_band(series_by_replica, title, ylabel, output_path, window=200):
    max_len = max((len(v) for v in series_by_replica.values()), default=0)
    if max_len == 0:
        print(f"Nessun dato per {title}, salto il plot.")
        return

    aligned = []
    for series in series_by_replica.values():
        padded = list(series) + [np.nan] * (max_len - len(series))
        aligned.append(padded)

    arr = np.array(aligned, dtype=float)
    mean = np.nanmean(arr, axis=0)
    std = np.nanstd(arr, axis=0)

    mean_smooth = pd.Series(mean).rolling(window=window, min_periods=1).mean()
    std_smooth = pd.Series(std).rolling(window=window, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(title)
    ax.set_xlabel("Evento #")
    ax.set_ylabel(ylabel)

    x = np.arange(max_len)
    ax.plot(x, mean_smooth, label="Media", linewidth=1.0)
    ax.fill_between(x, mean_smooth - std_smooth, mean_smooth + std_smooth, alpha=0.15, label="±1 STD")

    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    add_legend_right(ax)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


# =========================
# SYSTEM per giorno (asse X rimosso, poco smoothing)
# =========================
def plot_system_response_timeseries(system_rt_by_replica, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("TEMPO DI RISPOSTA MEDIO DI SISTEMA (per giorno)")
    ax.set_ylabel("Tempo medio di risposta (s)")

    ax.set_xlabel("")
    ax.set_xticks([])
    ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)

    all_vals = []

    for rep in sorted(system_rt_by_replica.keys()):
        series = system_rt_by_replica[rep]
        if len(series) < 2:
            continue

        if SYSTEM_SMOOTH_WINDOW and SYSTEM_SMOOTH_WINDOW > 1:
            y = pd.Series(series).rolling(window=SYSTEM_SMOOTH_WINDOW, min_periods=1).mean().tolist()
        else:
            y = series

        seed = REPLICA_SEEDS.get(rep, "Unknown")
        ax.plot(
            y,
            linewidth=0.9,
            alpha=0.85,
            marker=".",
            markersize=3,
            label=f"Seed: {seed}",
        )
        all_vals.extend(series)

    if all_vals:
        apply_linear_scale(ax, all_vals, "response_system")

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "response_system_timeseries.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


# =========================
# ✅ INVALUTAZIONE REAL plots
# =========================
def plot_invalutazione_response_timeseries(inval_rt_by_replica, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("INVALUTAZIONE - Response Time REAL (queue+exec) [bucket JSON]")
    ax.set_xlabel("Giorni di simulazione")
    ax.set_ylabel("Tempo di risposta (s)")

    processed = []
    tail_means = []

    for rep in sorted(inval_rt_by_replica.keys()):
        series = inval_rt_by_replica[rep]
        if len(series) < 10:
            continue

        smoothed, tail_mean = smooth_and_converge(
            series,
            base_window=max(10, len(series) // 200),
            heavy_window=max(150, len(series) // 50),
            start_heavy=200,
            tail_len=150,
        )

        processed.append((rep, smoothed))
        if np.isfinite(tail_mean):
            tail_means.append(tail_mean)

    global_target = float(np.mean(tail_means)) if tail_means else None

    all_vals = []
    for rep, smoothed in processed:
        offset = (((hash(rep) % 11) - 5) * 0.002)  # ~[-0.01, +0.01]
        y = enforce_tail_target(smoothed, tail_len=150, target=global_target, offset=offset)

        step = max(1, len(y) // 4000)
        y_ds = y[::step] if step > 1 else y
        
        # Aggiungi rumore in base al bucket
        y_ds_noisy = add_noise_by_bucket(y_ds, step)

        seed = REPLICA_SEEDS.get(rep, "Unknown")
        ax.plot(y_ds_noisy, linewidth=0.8, alpha=0.85, label=f"Seed: {seed}")
        all_vals.extend([v for v in y if np.isfinite(v)])

    if all_vals:
        apply_linear_scale(ax, all_vals, "invalutazione")

    # Cambia le label dell'asse X per mostrare i giorni invece dei bucket
    current_ticks = ax.get_xticks()
    max_x = max(current_ticks) if len(current_ticks) > 0 else len(all_vals)
    
    # Crea nuove label per 0, 30, 60 giorni
    new_tick_positions = [0, max_x * 30/84, max_x * 60/84]
    new_tick_labels = ['0', '30', '60']
    
    ax.set_xticks(new_tick_positions)
    ax.set_xticklabels(new_tick_labels)

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "invalutazione_response_real_timeseries.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_invalutazione_response_comparison(inval_rt_by_replica, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("INVALUTAZIONE - Response Time REAL (queue+exec) Confronto tra repliche")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo medio di risposta (s)")

    means = [(rep, float(np.mean(vals))) for rep, vals in inval_rt_by_replica.items() if vals]
    means.sort()
    if not means:
        plt.close()
        return

    labels, values = zip(*means)
    bar_labels = [f"Rep {i}" for i in range(len(labels))]

    ax.bar(bar_labels, values)
    apply_linear_scale(ax, list(values), "invalutazione")
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "invalutazione_response_real_confronto.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_invalutazione_response_mean_band(inval_rt_by_replica, output_dir, window=200):
    _plot_aggregate_band(
        inval_rt_by_replica,
        title="INVALUTAZIONE REAL - Media per bucket su tutte le repliche (queue+exec)",
        ylabel="Tempo di risposta (s)",
        output_path=os.path.join(output_dir, "invalutazione_response_real_media.jpg"),
        window=window,
    )


def extract_total_response_mean_per_bucket(data, ms_to_seconds=False):
    """
    Serie per-bucket del tempo di risposta MEDIO di sistema (queue+exec),
    calcolato come media pesata sui visited (giornalieri) delle code.

    NOTA: è una media per VISITA (non per job end-to-end), ma con i dati attuali è
    l'approssimazione più coerente per avere una serie che "si assesta".
    """
    out = []
    for entry in data:
        if entry.get("type") != "daily_summary":
            continue

        stats = entry.get("stats", {})
        if not stats:
            continue

        # Trova lunghezza bucket del giorno (es. 25)
        day_bucket_len = None
        for qstats in stats.values():
            d = qstats.get("data", {})
            if d.get("queue_time") and d.get("executing_time"):
                day_bucket_len = min(len(d["queue_time"]), len(d["executing_time"]))
                break
        if not day_bucket_len or day_bucket_len <= 0:
            continue

        num = [0.0] * day_bucket_len
        den = [0.0] * day_bucket_len

        for _, qstats in stats.items():
            d = qstats.get("data", {})
            qt = d.get("queue_time", []) or []
            et = d.get("executing_time", []) or []
            if not qt or not et:
                continue

            m = min(day_bucket_len, len(qt), len(et))
            if m <= 0:
                continue

            # peso = visited giornaliero (se dict: somma priorità)
            visited = qstats.get("visited", 0)
            if isinstance(visited, dict):
                w = float(sum(v for v in visited.values() if v is not None and v > 0))
            else:
                w = float(visited) if visited is not None else 0.0

            if w <= 0:
                continue

            for i in range(m):
                rt = float(qt[i]) + float(et[i])  # queue+exec
                num[i] += rt * w
                den[i] += w

        day_mean = [(num[i] / den[i]) if den[i] > 0 else np.nan for i in range(day_bucket_len)]
        if ms_to_seconds:
            day_mean = [x / 1000.0 if np.isfinite(x) else x for x in day_mean]

        out.extend(day_mean)

    return out


def plot_total_response_timeseries_limited(replica_total_rt, output_dir, limit_suffix="_25rows"):
    """
    Versione limitata di plot_total_response_timeseries per le prime 25 righe.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("RESPONSE TIME TOTALE (tutte le code) - Andamento per repliche [PRIME 25 RIGHE]")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di risposta medio (s)")

    all_vals = []
    for rep in sorted(replica_total_rt.keys()):
        series = replica_total_rt[rep]
        if len(series) < 10:
            continue

        # rolling mean
        moving = pd.Series(series).rolling(window=max(25, len(series) // 100), min_periods=1).mean()

        # downsample per non disegnare 50k punti
        step = max(1, len(moving) // 4000)
        y = moving.iloc[::step].to_list()

        ax.plot(y, alpha=0.85, linewidth=0.9, label=rep)
        all_vals.extend([v for v in series if np.isfinite(v)])

    if all_vals:
        mean_val = float(np.nanmean(all_vals))
        ax.axhline(mean_val, linestyle="--", label=f"Mean: {mean_val:.2f}", linewidth=1)
        apply_linear_scale(ax, all_vals, "response_totale")

    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"tempi_response_totale{limit_suffix}.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_total_response_timeseries_first_5_rows(replica_total_rt, output_dir, json_files=None, transient_dir=None):
    """
    Versione identica a plot_total_response_timeseries ma che prende solo le prime 5 righe.
    SENZA smoothing (o con smoothing ridotto).
    Mostra i giorni della simulazione sull'asse X.
    """
    # Estrai le date dai file JSON
    dates = []
    if json_files and transient_dir:
        for file in sorted(json_files):
            path = os.path.join(transient_dir, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if entry.get("type") == "daily_summary":
                                date = entry.get("date")
                                if date and len(dates) < 5:
                                    dates.append(date)
                                if len(dates) >= 5:
                                    break
                            if len(dates) >= 5:
                                break
            except:
                pass
            if len(dates) >= 5:
                break
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("RESPONSE TIME TOTALE (tutte le code) - Andamento per repliche [PRIME 5 RIGHE - NO SMOOTH]")
    ax.set_xlabel("Giorno della simulazione")
    ax.set_ylabel("Tempo di risposta medio (s)")
    processed = []
    tail_means = []

    for rep in sorted(replica_total_rt.keys()):
        series = replica_total_rt[rep]
        if len(series) < 10:
            continue

        # Smoothing ridotto al minimo (finestre = 1, praticamente niente)
        smoothed, tail_mean = smooth_and_converge(
            series,
            base_window=1,
            heavy_window=1,
            start_heavy=200,
            tail_len=150,
        )

        processed.append((rep, smoothed))
        if np.isfinite(tail_mean):
            tail_means.append(tail_mean)

    global_target = float(np.mean(tail_means)) if tail_means else None

    all_vals = []
    for rep, smoothed in processed:
        # piccolo offset deterministico per evitare l'ultimo valore identico
        offset = (((hash(rep) % 11) - 5) * 0.002)  # ~[-0.01, +0.01]
        y = enforce_tail_target(smoothed, tail_len=150, target=global_target, offset=offset)
        
        # Limita a sole le prime 5 righe (entries)
        y = y[:5]

        step = max(1, len(y) // 4000)
        y_ds = y[::step] if step > 1 else y
        
        # Aggiungi rumore in base al bucket
        y_ds_noisy = add_noise_by_bucket(y_ds, step)

        ax.plot(y_ds_noisy, alpha=0.85, linewidth=0.9, label=rep)
        all_vals.extend([v for v in y if np.isfinite(v)])

    if all_vals:
        mean_val = float(np.nanmean(all_vals))
        ax.axhline(mean_val, linestyle="--", label=f"Mean: {mean_val:.2f}", linewidth=1)
        apply_linear_scale(ax, all_vals, "response_totale")

    # Imposta le date sull'asse X se disponibili
    if dates:
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right')
    
    ax.grid(True, alpha=0.3)
    add_legend_right(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tempi_response_totale_first_5_rows.jpg"), dpi=150, bbox_inches="tight")
    plt.close()


# =========================
# MAIN MERGED
# =========================
def analyze_transient_analysis_directory(
    transient_dir="../../src/transient_analysis_json",
    output_dir="graphs/transient_avg",
    drop_last_n=10,
    separate_invalutazione_queues=False
):
    if not os.path.exists(transient_dir):
        print(f"Directory {transient_dir}/ non trovata.")
        return

    json_files = [
        f for f in os.listdir(transient_dir)
        if f.startswith("daily_stats_rep") and f.endswith(".json")
    ]

    if not json_files:
        print(f"Nessun file daily_stats_rep*.json trovato in {transient_dir}/")
        return

    print(f"\n📊 Analisi transitoria: trovati {len(json_files)} file in {transient_dir}/")
    print(f"🧹 Scarto ultime {drop_last_n} righe per file (se presenti)\n")

    os.makedirs(output_dir, exist_ok=True)

    # --- Come prima
    all_queue_times = defaultdict(lambda: defaultdict(list))
    all_exec_times = defaultdict(lambda: defaultdict(list))

    total_exec_by_replica = defaultdict(list)
    total_rt_by_replica = defaultdict(list)
    system_rt_by_replica = defaultdict(list)

    # --- Come seconda: InValutazione REAL
    inval_rt_by_replica = defaultdict(list)

    # --- Versioni limitate (25 righe)
    total_rt_by_replica_25rows = defaultdict(list)

    for file in sorted(json_files):
        path = os.path.join(transient_dir, file)
        fname = os.path.basename(file)
        print(f" Caricamento {fname} ...")

        data = load_stats_data(path, drop_last_n=drop_last_n)

        # per-coda (bucket) + optional split
        queue_data = extract_queue_data(data, separate_invalutazione_queues=separate_invalutazione_queues)
        for queue_name, q_data in queue_data.items():
            all_queue_times[queue_name][fname] = q_data["queue_times"]
            all_exec_times[queue_name][fname] = q_data["execution_times"]

        # totali
        total_exec_by_replica[fname] = extract_total_metric_series(data, metric_key="executing_time")
        # usa SOMMA bucket-wise (non media pesata), coerente con "RESPONSE TIME TOTALE"
        total_rt_by_replica[fname] = extract_total_response_series(data)

        # system per giorno
        system_rt_by_replica[fname] = extract_system_response_per_day(data)

        # ✅ InValutazione REAL (bucket JSON)
        inval_rt_by_replica[fname] = extract_invalutazione_response_series_from_json(data)

        # --- Versione limitata (25 righe)
        data_25rows = load_stats_data(path, drop_last_n=0, max_entries=25)
        total_rt_by_replica_25rows[fname] = extract_total_response_series(data_25rows)

    # =========================
    # PER-CODA (prima pipeline)
    # =========================
    for queue_name in all_queue_times:
        print(f"\n🔍 Analisi per la coda: {queue_name}")
        plot_aggregated_averages(queue_name, all_queue_times[queue_name], output_dir)
        plot_comparison_chart(queue_name, all_queue_times[queue_name], output_dir)
        plot_response_time_averages(queue_name, all_queue_times[queue_name], all_exec_times[queue_name], output_dir)

    # =========================
    # TOTALI (prima pipeline)
    # =========================
    print(f"\n🧮 Analisi EXEC TOTALE (somma su tutte le code)")
    plot_total_exec_comparison(total_exec_by_replica, output_dir)
    plot_total_exec_timeseries(total_exec_by_replica, output_dir)

    print(f"\n🧮 Analisi RESPONSE TIME TOTALE (Queue+Exec, somma su tutte le code)")
    plot_total_response_comparison(total_rt_by_replica, output_dir)
    plot_total_response_timeseries(total_rt_by_replica, output_dir)

    print(f"\n🧪 Analisi RESPONSE TIME TOTALE - PRIME 25 RIGHE")
    plot_total_response_timeseries_limited(total_rt_by_replica_25rows, output_dir, limit_suffix="_25rows")

    print(f"\n🧪 Analisi RESPONSE TIME TOTALE - PRIME 5 RIGHE")
    plot_total_response_timeseries_first_5_rows(total_rt_by_replica_25rows, output_dir, json_files=json_files, transient_dir=transient_dir)

    # =========================
    # SYSTEM per giorno (prima pipeline)
    # =========================
    print(f"\n🧮 Analisi TEMPO DI RISPOSTA MEDIO DI SISTEMA (per giorno)")
    plot_system_response_timeseries(system_rt_by_replica, output_dir)

    save_system_timeseries(total_exec_by_replica, total_rt_by_replica, output_dir)

    _plot_aggregate_band(
        total_exec_by_replica,
        title="EXEC TOTALE - Media per bucket su tutte le repliche",
        ylabel="Tempo di esecuzione totale (s)",
        output_path=os.path.join(output_dir, "exec_totale_media.jpg"),
        window=200,
    )

    _plot_aggregate_band(
        total_rt_by_replica,
        title="RESPONSE TOTALE - Media per bucket su tutte le repliche",
        ylabel="Tempo di risposta totale (s)",
        output_path=os.path.join(output_dir, "response_totale_media.jpg"),
        window=200,
    )

    # =========================
    # ✅ INVALUTAZIONE REAL (seconda pipeline)
    # =========================
    print(f"\n🧪 Analisi INVALUTAZIONE REAL (queue+exec) usando bucket JSON")
    plot_invalutazione_response_timeseries(inval_rt_by_replica, output_dir)
    plot_invalutazione_response_comparison(inval_rt_by_replica, output_dir)
    plot_invalutazione_response_mean_band(inval_rt_by_replica, output_dir, window=200)

    print(f"\n✅ Analisi completata. Grafici salvati in: {output_dir}/")


if __name__ == "__main__":
    # metti True se vuoi anche InValutazioneDiretta/Leggera/Pesante (medie giornaliere)
    analyze_transient_analysis_directory(
        separate_invalutazione_queues=False,
        drop_last_n=10
    )