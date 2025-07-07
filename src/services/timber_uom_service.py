from decimal import Decimal
from typing import Dict, Optional
from src.models.user import db
from src.models.stock import StockItem, StockUOM
import logging

logger = logging.getLogger(__name__)

class TimberUOMService:
    """
    Service to handle timber UOM conversions (m3 to pieces) and stock length calculations.
    """

    @staticmethod
    def convert_m3_to_pieces(m3_quantity: Decimal, stock_item_id: int) -> Decimal:
        """
        Converts a quantity in cubic meters (m3) to pieces for a given timber stock item.
        Requires the stock item to have defined dimensions (e.g., thickness, width, length).
        """
        stock_item = db.session.query(StockItem).filter_by(id=stock_item_id).first()
        if not stock_item:
            raise ValueError(f"Stock item with ID {stock_item_id} not found.")

        # Assuming stock item has dimensions stored in its properties or a related table
        # For simplicity, let's assume dimensions are part of the stock item for now.
        # In a real system, these might be attributes or part of a product variant.
        thickness_mm = stock_item.get_property("thickness_mm") # Example: 38
        width_mm = stock_item.get_property("width_mm")       # Example: 76
        length_m = stock_item.get_property("length_m")       # Example: 3.6

        if not all([thickness_mm, width_mm, length_m]):
            raise ValueError(f"Timber stock item {stock_item.code} is missing dimension properties for m3 conversion.")

        # Calculate volume of one piece in m3
        piece_volume_m3 = (Decimal(str(thickness_mm)) / 1000) * \
                          (Decimal(str(width_mm)) / 1000) * \
                          Decimal(str(length_m))

        if piece_volume_m3 == 0:
            raise ValueError(f"Calculated piece volume for {stock_item.code} is zero.")

        pieces = m3_quantity / piece_volume_m3
        logger.info(f"Converted {m3_quantity} m3 to {pieces} pieces for {stock_item.code}")
        return pieces

    @staticmethod
    def convert_actual_length_to_stock_pieces(total_actual_length_m: Decimal, 
                                              target_stock_code: str) -> Dict:
        """
        Converts a total actual length (e.g., for battens) into a quantity of specific stock pieces.
        Returns the calculated quantity and the stock item.
        """
        stock_item = db.session.query(StockItem).filter_by(code=target_stock_code).first()
        if not stock_item:
            raise ValueError(f"Target stock item {target_stock_code} not found.")

        length_m = stock_item.get_property("length_m") # Example: 3.6

        if not length_m or Decimal(str(length_m)) == 0:
            raise ValueError(f"Stock item {stock_item.code} is missing length property for actual length conversion.")

        # Calculate number of pieces needed, rounding up to ensure enough material
        pieces_needed = (total_actual_length_m / Decimal(str(length_m))).quantize(Decimal("1."), rounding=ROUND_UP)
        
        logger.info(f"Converted {total_actual_length_m}m actual length to {pieces_needed} pieces of {stock_item.code}")
        return {
            "stock_item": stock_item,
            "quantity": pieces_needed
        }

    @staticmethod
    def get_stock_item_by_dimensions(thickness_mm: int, width_mm: int, length_m: Decimal, stock_type_name: str = "Timber") -> Optional[StockItem]:
        """
        Finds a timber stock item based on its dimensions and stock type.
        This assumes stock items have properties like 'thickness_mm', 'width_mm', 'length_m'.
        """
        # This is a placeholder. In a real system, you'd query based on a more robust
        # attribute system or a specific coding convention for timber.
        # For example, stock.code might be 'TIM-38x76x3.6'
        
        # First, find the StockType ID for 'Timber'
        timber_stock_type = db.session.query(StockUOM).filter_by(name=stock_type_name).first()
        if not timber_stock_type:
            logger.warning(f"Stock type "{stock_type_name}" not found.")
            return None

        # Construct a search pattern or query based on assumed stock item properties
        # This part needs to be aligned with how your stock items are actually stored
        # For demonstration, let's assume a property-based lookup or a code pattern
        
        # Example: Querying based on assumed properties (requires StockItem to have these)
        # For this to work, StockItem model needs to be extended with a way to store/query properties
        # For now, let's return a dummy or search by code if a pattern is known
        
        # A more realistic approach would be to have a separate StockAttribute model
        # or to parse the stock code itself if it contains dimensions.
        
        # For now, let's assume stock codes follow a pattern like 'TIM-38x76x3.6'
        search_code_pattern = f"TIM-{thickness_mm}x{width_mm}x{length_m}"
        
        stock_item = db.session.query(StockItem).filter(
            StockItem.stock_type_id == timber_stock_type.id,
            StockItem.code.ilike(f"%{search_code_pattern}%")
        ).first()
        
        if not stock_item:
            logger.warning(f"No stock item found for timber {thickness_mm}x{width_mm}x{length_m}m.")
            
        return stock_item


# Add ROUND_UP to the global scope for use in the service
from decimal import ROUND_UP


