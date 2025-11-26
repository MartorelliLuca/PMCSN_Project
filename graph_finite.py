#!/usr/bin/env python3
"""
Read per-day JSON replicas from src/transient_analysis_json/ (files named like
`daily_stats_rep0.json`) and plot the system response (avg time in system)
by day and by month, aggregating across replicas and showing 95% CI.

Assumptions:
- Each JSON file is newline-delimited JSON where daily summaries have
  type == 'daily_summary' and contain 'date' and 'stats'.
- For each service in 'stats', fields include 'visited', 'queue_time'
  and 'executing_time'. We compute per-service total_time = queue_time + executing_time
  (these appear to be totals for that day) and per-day system average
  response = sum(service_total_time) / sum(service_visited).

Outputs:
- graphs/response_by_day.png
- graphs/response_by_month.png

Usage: run the script from the repo root. Optional args --input-dir and --out-dir.
"""

import os
import glob
import json
from datetime import datetime
from collections import defaultdict
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_replica_file(path):
	"""Read one replica file and return dict date_str -> avg_response_seconds"""
	date_to_response = {}
	with open(path, 'r') as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			try:
				obj = json.loads(line)
			except Exception:
				# skip non-json lines
				continue
			if obj.get('type') != 'daily_summary':
				continue
			date = obj.get('date')
			stats = obj.get('stats', {}) or {}
			total_visits = 0
			total_time = 0.0
			for svc, svc_stats in stats.items():
				visited = svc_stats.get('visited', 0)
				queue_time = svc_stats.get('queue_time', 0.0) or 0.0
				executing_time = svc_stats.get('executing_time', 0.0) or 0.0
				total_visits += visited
				total_time += (queue_time + executing_time)
			if total_visits > 0:
				#avg_response = total_time / total_visits
				date_to_response[date] = total_time 
			else:
				# no visits; store NaN
				date_to_response[date] = float('nan')
	return date_to_response


def collect_replicas(input_dir):
	pattern = os.path.join(input_dir, 'daily_stats_rep*.json')
	files = sorted(glob.glob(pattern))
	replicas = []
	for p in files:
		replicas.append(read_replica_file(p))
	return replicas, files


def build_dataframe(replicas):
	"""Build a DataFrame where rows are dates and columns are replicas."""
	# collect all dates
	all_dates = set()
	for rep in replicas:
		all_dates.update(rep.keys())
	# sort dates
	def parse_date(s):
		try:
			return datetime.strptime(s, '%Y-%m-%d')
		except Exception:
			# try fallback
			return datetime.fromisoformat(s)

	sorted_dates = sorted(all_dates, key=parse_date)
	df = pd.DataFrame(index=[d for d in sorted_dates])
	for i, rep in enumerate(replicas):
		series = pd.Series({d: rep.get(d, np.nan) for d in sorted_dates})
		df[f'rep{i}'] = series.values
	# convert index to datetime
	df.index = pd.to_datetime(df.index)
	return df


def compute_stats(df):
	"""Compatibility placeholder kept for older calls. Not used when plotting all replicas.
	Returns empty DataFrame.
	"""
	return pd.DataFrame()


def aggregate_monthly_per_replica(df):
	"""Return a DataFrame of monthly averages for each replica column.

	Input: df with datetime index and columns rep0..repN.
	Output: monthly_df with datetime index at month-end and same replica columns.
	"""
	# Ensure datetime index
	monthly = df.resample('M').mean()
	return monthly


def plot_replicas_daily(df, outpath, title='Replica responses by day'):
	"""Plot every replica as a separate line on the same daily plot."""
	plt.figure(figsize=(14, 6))
	for col in df.columns:
		plt.plot(df.index, df[col], label=col, alpha=0.7)
	plt.title(title)
	plt.xlabel('Date')
	plt.ylabel('Response (s)')
	plt.grid(alpha=0.3)
	plt.legend(ncol=2, fontsize='small')
	plt.tight_layout()
	plt.savefig(outpath)
	plt.close()


def plot_replicas_monthly(monthly_df, outpath, title='Replica responses by month'):
	plt.figure(figsize=(14, 6))
	for col in monthly_df.columns:
		plt.plot(monthly_df.index, monthly_df[col], label=col, alpha=0.8)
	plt.title(title)
	plt.xlabel('Month')
	plt.ylabel('Avg response (s)')
	plt.grid(alpha=0.3)
	plt.legend(ncol=2, fontsize='small')
	plt.tight_layout()
	plt.savefig(outpath)
	plt.close()


def ensure_dir(d):
	if not os.path.exists(d):
		os.makedirs(d, exist_ok=True)


def main(input_dir='src/transient_analysis_json', out_dir='graphs'):
	print(f'Reading replicas from: {input_dir}')
	replicas, files = collect_replicas(input_dir)
	if not replicas:
		print('No replica files found. Looked for daily_stats_rep*.json')
		return
	print(f'Found {len(replicas)} replica files')
	df = build_dataframe(replicas)

	ensure_dir(out_dir)

	# daily plot: every replica as its own line
	out_daily = os.path.join(out_dir, 'response_by_day_replicas.png')
	plot_replicas_daily(df, out_daily, title='Replica responses by day (system-wide)')
	print(f'Wrote {out_daily}')

	# monthly aggregation per-replica and plot
	monthly = aggregate_monthly_per_replica(df)
	out_month = os.path.join(out_dir, 'response_by_month_replicas.png')
	plot_replicas_monthly(monthly, out_month, title='Replica responses by month (system-wide)')
	print(f'Wrote {out_month}')


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Plot system response by day and month from replica JSONs')
	parser.add_argument('--input-dir', default='src/finite_horizon_json_base', help='Folder containing daily_stats_rep*.json')
	parser.add_argument('--out-dir', default='graphs', help='Output folder for plots')
	args = parser.parse_args()
	main(args.input_dir, args.out_dir)

