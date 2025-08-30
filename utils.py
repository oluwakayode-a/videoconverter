import subprocess
import os
import platform
import shutil
import re
import urllib.request
import zipfile
import tarfile
import tempfile
from pathlib import Path

class FFmpegHandler:
    """Handles FFmpeg installation and detection across platforms"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.ffmpeg_urls = {
            "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            "darwin": "https://evermeet.cx/ffmpeg/ffmpeg-6.0.zip",  # macOS
            "linux": None  # Will use package manager
        }
    
    def is_ffmpeg_installed(self):
        """Check if FFmpeg is installed and accessible"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def install_ffmpeg(self):
        """Install FFmpeg based on the operating system"""
        try:
            if self.system == "windows":
                return self._install_ffmpeg_windows()
            elif self.system == "darwin":  # macOS
                return self._install_ffmpeg_macos()
            elif self.system == "linux":
                return self._install_ffmpeg_linux()
            else:
                print(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            print(f"FFmpeg installation failed: {e}")
            return False
    
    def _install_ffmpeg_windows(self):
        """Install FFmpeg on Windows"""
        print("Installing FFmpeg for Windows...")
        
        # Create ffmpeg directory in user's home
        ffmpeg_dir = Path.home() / "ffmpeg"
        ffmpeg_dir.mkdir(exist_ok=True)
        
        # Download FFmpeg
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"
            
            print("Downloading FFmpeg...")
            urllib.request.urlretrieve(self.ffmpeg_urls["windows"], zip_path)
            
            print("Extracting FFmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the extracted folder
            extracted_folders = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
            if not extracted_folders:
                raise Exception("Could not find extracted FFmpeg folder")
            
            ffmpeg_extracted = extracted_folders[0]
            bin_dir = ffmpeg_extracted / "bin"
            
            if not bin_dir.exists():
                raise Exception("Could not find FFmpeg bin directory")
            
            # Copy to destination
            destination_bin = ffmpeg_dir / "bin"
            if destination_bin.exists():
                shutil.rmtree(destination_bin)
            shutil.copytree(bin_dir, destination_bin)
        
        # Add to PATH
        self._add_to_path_windows(str(destination_bin))
        
        print("FFmpeg installation completed!")
        return True
    
    def _install_ffmpeg_macos(self):
        """Install FFmpeg on macOS"""
        print("Installing FFmpeg for macOS...")
        
        # Try Homebrew first
        try:
            result = subprocess.run(["brew", "--version"], capture_output=True)
            if result.returncode == 0:
                print("Installing via Homebrew...")
                result = subprocess.run(["brew", "install", "ffmpeg"], capture_output=True, text=True)
                if result.returncode == 0:
                    return True
        except FileNotFoundError:
            pass
        
        # Fallback to manual installation
        ffmpeg_dir = Path.home() / "ffmpeg"
        ffmpeg_dir.mkdir(exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "ffmpeg.zip"
            
            print("Downloading FFmpeg...")
            urllib.request.urlretrieve(self.ffmpeg_urls["darwin"], zip_path)
            
            print("Extracting FFmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Copy ffmpeg binary
            ffmpeg_binary = Path(temp_dir) / "ffmpeg"
            destination = ffmpeg_dir / "ffmpeg"
            shutil.copy2(ffmpeg_binary, destination)
            
            # Make executable
            os.chmod(destination, 0o755)
        
        # Add to PATH
        self._add_to_path_unix(str(ffmpeg_dir))
        
        print("FFmpeg installation completed!")
        return True
    
    def _install_ffmpeg_linux(self):
        """Install FFmpeg on Linux using package manager"""
        print("Installing FFmpeg for Linux...")
        
        # Try different package managers
        package_managers = [
            (["apt", "update"], ["apt", "install", "-y", "ffmpeg"]),  # Ubuntu/Debian
            (["yum", "check-update"], ["yum", "install", "-y", "ffmpeg"]),  # CentOS/RHEL
            (["dnf", "check-update"], ["dnf", "install", "-y", "ffmpeg"]),  # Fedora
            (["pacman", "-Sy"], ["pacman", "-S", "--noconfirm", "ffmpeg"]),  # Arch
            (["zypper", "refresh"], ["zypper", "install", "-y", "ffmpeg"])  # openSUSE
        ]
        
        for update_cmd, install_cmd in package_managers:
            try:
                # Test if package manager exists
                subprocess.run(update_cmd[:1] + ["--version"], capture_output=True, check=True)
                
                print(f"Using {update_cmd[0]} package manager...")
                
                # Update package list
                subprocess.run(update_cmd, capture_output=True, check=True)
                
                # Install FFmpeg
                result = subprocess.run(install_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("FFmpeg installation completed!")
                    return True
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # If all package managers fail, try snap
        try:
            subprocess.run(["snap", "install", "ffmpeg"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        print("Could not install FFmpeg automatically. Please install manually.")
        return False
    
    def _add_to_path_windows(self, path):
        """Add path to Windows PATH environment variable"""
        try:
            # Get current PATH
            result = subprocess.run(
                ["powershell", "-Command", "[Environment]::GetEnvironmentVariable('PATH', 'User')"],
                capture_output=True, text=True
            )
            current_path = result.stdout.strip()
            
            if path not in current_path:
                new_path = f"{current_path};{path}" if current_path else path
                subprocess.run([
                    "powershell", "-Command",
                    f"[Environment]::SetEnvironmentVariable('PATH', '{new_path}', 'User')"
                ], capture_output=True)
                
                # Also set for current session
                os.environ["PATH"] = f"{os.environ.get('PATH', '')};{path}"
        except Exception as e:
            print(f"Could not add to PATH: {e}")
    
    def _add_to_path_unix(self, path):
        """Add path to Unix PATH environment variable"""
        try:
            # Add to current session
            current_path = os.environ.get("PATH", "")
            if path not in current_path:
                os.environ["PATH"] = f"{current_path}:{path}"
            
            # Try to add to shell profile
            home = Path.home()
            shell_profiles = [".bashrc", ".zshrc", ".profile"]
            
            for profile in shell_profiles:
                profile_path = home / profile
                if profile_path.exists():
                    with open(profile_path, "a") as f:
                        f.write(f'\nexport PATH="$PATH:{path}"\n')
                    break
        except Exception as e:
            print(f"Could not add to PATH: {e}")


class VideoProcessor:
    """Handles video processing and conversion"""
    
    def __init__(self):
        self.supported_formats = {
            ".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", 
            ".wmv", ".m4v", ".3gp", ".mpg", ".mpeg", ".ts", ".mts"
        }
    
    def detect_format(self, file_path):
        """Detect the format of a video file"""
        try:
            extension = Path(file_path).suffix.lower()
            if extension in self.supported_formats:
                return extension[1:]  # Remove the dot
            
            # Use ffprobe to detect format if extension is unknown
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                format_name = data.get("format", {}).get("format_name", "unknown")
                return format_name.split(",")[0]  # Take first format if multiple
            
        except Exception:
            pass
        
        return "unknown"
    
    def convert_video(self, input_file, output_file, output_format, progress_callback=None):
        """Convert a video file to the specified format"""
        try:
            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-i", input_file,
                "-c:v", "libx264",  # Video codec
                "-c:a", "aac",      # Audio codec
                "-preset", "medium", # Encoding speed/quality balance
                "-crf", "23",       # Quality (lower = better quality)
                "-movflags", "+faststart",  # Web optimization
                "-y",               # Overwrite output file
                output_file
            ]
            
            # Add format-specific options
            if output_format.lower() == "webm":
                cmd[5:7] = ["-c:v", "libvpx-vp9", "-c:a", "libopus"]
            elif output_format.lower() in ["mov", "m4v"]:
                cmd[5:7] = ["-c:v", "libx264", "-c:a", "aac"]
            
            print(f"Running command: {' '.join(cmd)}")
            
            # Run conversion with progress tracking
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                universal_newlines=True
            )
            
            # Parse progress from stderr
            duration = self._get_video_duration(input_file)
            
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                
                if progress_callback and duration:
                    time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', line)
                    if time_match:
                        hours, minutes, seconds, centiseconds = map(int, time_match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                        progress = (current_time / duration) * 100
                        progress_callback(min(progress, 100))
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0 and os.path.exists(output_file):
                return True
            else:
                print(f"FFmpeg failed with return code: {return_code}")
                return False
                
        except Exception as e:
            print(f"Conversion error: {e}")
            return False
    
    def _get_video_duration(self, file_path):
        """Get video duration in seconds"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "compact=p=0:nk=1",
                "-show_entries", "format=duration", file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration_str = result.stdout.strip()
                return float(duration_str) if duration_str else None
        except Exception:
            pass
        return None


def main():
    """Entry point for standalone execution"""
    from main import VideoConverterApp
    app = VideoConverterApp()
    app.run()

if __name__ == "__main__":
    main()