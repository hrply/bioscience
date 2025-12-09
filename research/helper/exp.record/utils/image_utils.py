"""
图像处理工具 - 处理和转换图像文件
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import base64
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 检查可用的图像处理库
        self.available_libraries = []
        if PIL_AVAILABLE:
            self.available_libraries.append("pil")
        if OPENCV_AVAILABLE:
            self.available_libraries.append("opencv")
        
        if not self.available_libraries:
            self.logger.warning("No image processing libraries available")
    
    def is_available(self) -> bool:
        """检查图像处理功能是否可用"""
        return len(self.available_libraries) > 0
    
    def load_image(self, image_path: str) -> Any:
        """加载图像"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            if PIL_AVAILABLE:
                return Image.open(image_path)
            elif OPENCV_AVAILABLE:
                image = cv2.imread(str(image_path))
                if image is None:
                    raise ValueError("Failed to load image with OpenCV")
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        except Exception as e:
            self.logger.error(f"Error loading image {image_path}: {e}")
            raise
    
    def save_image(self, image: Any, output_path: str, format: str = "PNG", quality: int = 95) -> bool:
        """保存图像"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if PIL_AVAILABLE and hasattr(image, 'save'):
                # PIL图像
                save_kwargs = {}
                if format.upper() == "JPEG":
                    save_kwargs["quality"] = quality
                    save_kwargs["optimize"] = True
                
                image.save(output_path, format=format, **save_kwargs)
            
            elif OPENCV_AVAILABLE and isinstance(image, np.ndarray):
                # OpenCV图像
                if format.upper() == "PNG":
                    cv2.imwrite(str(output_path), image)
                elif format.upper() == "JPEG":
                    cv2.imwrite(str(output_path), image, [cv2.IMWRITE_JPEG_QUALITY, quality])
                else:
                    cv2.imwrite(str(output_path), image)
            
            else:
                raise ValueError("Unsupported image format")
            
            self.logger.info(f"Image saved to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving image to {output_path}: {e}")
            return False
    
    def resize_image(self, image: Any, width: int, height: int, maintain_aspect: bool = True) -> Any:
        """调整图像大小"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        try:
            if PIL_AVAILABLE and hasattr(image, 'resize'):
                if maintain_aspect:
                    image.thumbnail((width, height), Image.Resampling.LANCZOS)
                    return image
                else:
                    return image.resize((width, height), Image.Resampling.LANCZOS)
            
            elif OPENCV_AVAILABLE and isinstance(image, np.ndarray):
                if maintain_aspect:
                    h, w = image.shape[:2]
                    aspect_ratio = w / h
                    
                    new_width = width
                    new_height = int(width / aspect_ratio)
                    
                    if new_height > height:
                        new_height = height
                        new_width = int(height * aspect_ratio)
                    
                    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                else:
                    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            raise
    
    def crop_image(self, image: Any, x: int, y: int, width: int, height: int) -> Any:
        """裁剪图像"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        try:
            if PIL_AVAILABLE and hasattr(image, 'crop'):
                return image.crop((x, y, x + width, y + height))
            
            elif OPENCV_AVAILABLE and isinstance(image, np.ndarray):
                h, w = image.shape[:2]
                
                # 确保坐标在图像范围内
                x = max(0, min(x, w))
                y = max(0, min(y, h))
                width = min(width, w - x)
                height = min(height, h - y)
                
                return image[y:y+height, x:x+width]
        
        except Exception as e:
            self.logger.error(f"Error cropping image: {e}")
            raise
    
    def rotate_image(self, image: Any, angle: float) -> Any:
        """旋转图像"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        try:
            if PIL_AVAILABLE and hasattr(image, 'rotate'):
                return image.rotate(angle, expand=True)
            
            elif OPENCV_AVAILABLE and isinstance(image, np.ndarray):
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                
                # 计算旋转矩阵
                matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # 计算新的边界框
                cos = abs(matrix[0, 0])
                sin = abs(matrix[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))
                
                # 调整旋转矩阵
                matrix[0, 2] += (new_w / 2) - center[0]
                matrix[1, 2] += (new_h / 2) - center[1]
                
                return cv2.warpAffine(image, matrix, (new_w, new_h))
        
        except Exception as e:
            self.logger.error(f"Error rotating image: {e}")
            raise
    
    def enhance_image(self, image: Any, brightness: float = 1.0, contrast: float = 1.0, 
                     sharpness: float = 1.0, color: float = 1.0) -> Any:
        """增强图像"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL library required for image enhancement")
        
        try:
            enhanced = image
            
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(enhanced)
                enhanced = enhancer.enhance(brightness)
            
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = enhancer.enhance(contrast)
            
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(sharpness)
            
            if color != 1.0:
                enhancer = ImageEnhance.Color(enhanced)
                enhanced = enhancer.enhance(color)
            
            return enhanced
        
        except Exception as e:
            self.logger.error(f"Error enhancing image: {e}")
            raise
    
    def convert_to_grayscale(self, image: Any) -> Any:
        """转换为灰度图像"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        try:
            if PIL_AVAILABLE and hasattr(image, 'convert'):
                return image.convert('L')
            
            elif OPENCV_AVAILABLE and isinstance(image, np.ndarray):
                if len(image.shape) == 3:
                    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                else:
                    return image
        
        except Exception as e:
            self.logger.error(f"Error converting to grayscale: {e}")
            raise
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """获取图像信息"""
        if not self.is_available():
            raise RuntimeError("No image processing libraries available")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        info = {}
        
        try:
            # 文件信息
            stat = image_path.stat()
            info["file_size"] = stat.st_size
            info["file_format"] = image_path.suffix.upper()
            
            # 图像信息
            if PIL_AVAILABLE:
                with Image.open(image_path) as img:
                    info["width"] = img.width
                    info["height"] = img.height
                    info["mode"] = img.mode
                    info["format"] = img.format
                    
                    # 获取EXIF数据
                    if hasattr(img, '_getexif') and img._getexif():
                        exif_data = {}
                        for tag_id, value in img._getexif().items():
                            tag = TAGS.get(tag_id, tag_id)
                            exif_data[tag] = value
                        info["exif"] = exif_data
            
            elif OPENCV_AVAILABLE:
                image = cv2.imread(str(image_path))
                if image is not None:
                    h, w = image.shape[:2]
                    info["width"] = w
                    info["height"] = h
                    info["channels"] = image.shape[2] if len(image.shape) == 3 else 1
        
        except Exception as e:
            self.logger.error(f"Error getting image info: {e}")
        
        return info
    
    def image_to_base64(self, image: Any, format: str = "PNG") -> str:
        """将图像转换为base64字符串"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL library required for base64 conversion")
        
        try:
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            image_bytes = buffer.getvalue()
            base64_str = base64.b64encode(image_bytes).decode()
            
            return f"data:image/{format.lower()};base64,{base64_str}"
        
        except Exception as e:
            self.logger.error(f"Error converting image to base64: {e}")
            raise
    
    def base64_to_image(self, base64_str: str) -> Any:
        """将base64字符串转换为图像"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL library required for base64 conversion")
        
        try:
            # 移除data URL前缀
            if base64_str.startswith('data:'):
                base64_str = base64_str.split(',')[1]
            
            image_bytes = base64.b64decode(base64_str)
            buffer = io.BytesIO(image_bytes)
            
            return Image.open(buffer)
        
        except Exception as e:
            self.logger.error(f"Error converting base64 to image: {e}")
            raise
    
    def create_thumbnail(self, image: Any, size: Tuple[int, int] = (128, 128)) -> Any:
        """创建缩略图"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL library required for thumbnail creation")
        
        try:
            # 创建副本以避免修改原图
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            return thumbnail
        
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            raise
    
    def apply_filter(self, image: Any, filter_type: str) -> Any:
        """应用滤镜"""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL library required for filters")
        
        try:
            if filter_type == "blur":
                return image.filter(ImageFilter.BLUR)
            elif filter_type == "sharpen":
                return image.filter(ImageFilter.SHARPEN)
            elif filter_type == "edge_enhance":
                return image.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_type == "smooth":
                return image.filter(ImageFilter.SMOOTH)
            elif filter_type == "emboss":
                return image.filter(ImageFilter.EMBOSS)
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
        
        except Exception as e:
            self.logger.error(f"Error applying filter {filter_type}: {e}")
            raise
    
    def is_valid_image(self, image_path: str) -> bool:
        """检查图像文件是否有效"""
        if not self.is_available():
            return False
        
        image_path = Path(image_path)
        if not image_path.exists():
            return False
        
        try:
            if PIL_AVAILABLE:
                with Image.open(image_path) as img:
                    img.verify()
                    return True
            
            elif OPENCV_AVAILABLE:
                image = cv2.imread(str(image_path))
                return image is not None
        
        except Exception as e:
            self.logger.error(f"Image validation error: {e}")
            return False
        
        return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的图像格式"""
        if not PIL_AVAILABLE:
            return []
        
        try:
            # PIL支持的格式
            supported_formats = []
            
            # 常见格式
            common_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP']
            
            for fmt in common_formats:
                if hasattr(Image, f'_{fmt.upper()}'):
                    supported_formats.append(fmt)
            
            return supported_formats
        
        except Exception as e:
            self.logger.error(f"Error getting supported formats: {e}")
            return []


# 全局图像处理器实例
_global_image_processor = None


def get_image_processor() -> ImageProcessor:
    """获取全局图像处理器实例"""
    global _global_image_processor
    if _global_image_processor is None:
        _global_image_processor = ImageProcessor()
    return _global_image_processor