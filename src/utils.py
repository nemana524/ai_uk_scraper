"""
Utility functions for the Companies House scraper.
"""
import os
import sys
import time
import logging
import shutil
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def get_disk_space(path: str = '.') -> Tuple[float, float, float]:
    """
    Get disk space information for the specified path.
    
    Args:
        path: Path to check disk space for
        
    Returns:
        Tuple of (total_space_gb, used_space_gb, free_space_gb)
    """
    disk = shutil.disk_usage(path)
    total_gb = disk.total / (1024 ** 3)
    used_gb = disk.used / (1024 ** 3)
    free_gb = disk.free / (1024 ** 3)
    return (total_gb, used_gb, free_gb)

def monitor_resources(data_dir: str, warn_threshold_gb: float = 10.0) -> Dict[str, Any]:
    """
    Monitor system resources and return a status report.
    
    Args:
        data_dir: Directory where data is being stored
        warn_threshold_gb: Threshold in GB to warn about low disk space
        
    Returns:
        Dictionary with resource usage information
    """
    # Get disk space
    total_gb, used_gb, free_gb = get_disk_space(data_dir)
    
    # Get memory usage
    mem = psutil.virtual_memory()
    mem_total_gb = mem.total / (1024 ** 3)
    mem_used_gb = mem.used / (1024 ** 3)
    mem_percent = mem.percent
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Create resource report
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'disk': {
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'percent_used': round((used_gb / total_gb) * 100, 2) if total_gb > 0 else 0
        },
        'memory': {
            'total_gb': round(mem_total_gb, 2),
            'used_gb': round(mem_used_gb, 2),
            'percent_used': mem_percent
        },
        'cpu': {
            'percent_used': cpu_percent
        }
    }
    
    # Check if disk space is running low
    if free_gb < warn_threshold_gb:
        logger.warning(f"Low disk space: {free_gb:.2f} GB free (below {warn_threshold_gb} GB threshold)")
    
    return report

def calculate_eta(start_time: float, total_processed: int, total_estimated: int) -> str:
    """
    Calculate estimated time to completion based on current progress.
    
    Args:
        start_time: Start time in seconds (from time.time())
        total_processed: Number of items processed so far
        total_estimated: Estimated total number of items
        
    Returns:
        String representation of estimated time remaining
    """
    if total_processed == 0:
        return "Unknown"
    
    elapsed = time.time() - start_time
    items_per_second = total_processed / elapsed
    
    if items_per_second == 0:
        return "Unknown"
    
    remaining_items = total_estimated - total_processed
    seconds_remaining = remaining_items / items_per_second
    
    # Convert seconds to a readable format
    if seconds_remaining < 60:
        return f"{int(seconds_remaining)} seconds"
    elif seconds_remaining < 3600:
        return f"{int(seconds_remaining / 60)} minutes"
    elif seconds_remaining < 86400:
        return f"{int(seconds_remaining / 3600)} hours"
    else:
        return f"{int(seconds_remaining / 86400)} days"

def get_company_count_estimate() -> int:
    """
    Get an estimated count of UK companies based on Companies House statistics.
    
    Returns:
        Estimated number of companies
    """
    # As of last update, there were approximately 4.8 million companies
    # This is a rough estimate and may need to be updated
    return 4800000

def format_memory_size(size_bytes: int) -> str:
    """
    Format a memory size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable string representation
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

def get_directory_size(directory: str) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

def print_resource_report(report: Dict[str, Any]) -> None:
    """
    Print a formatted resource report.
    
    Args:
        report: Resource report dictionary
    """
    print("\n===== RESOURCE REPORT =====")
    print(f"Time: {report['timestamp']}")
    print(f"Disk: {report['disk']['free_gb']:.2f} GB free / {report['disk']['total_gb']:.2f} GB total ({report['disk']['percent_used']}% used)")
    print(f"Memory: {report['memory']['used_gb']:.2f} GB used / {report['memory']['total_gb']:.2f} GB total ({report['memory']['percent_used']}% used)")
    print(f"CPU: {report['cpu']['percent_used']}% used")
    print("==========================\n") 