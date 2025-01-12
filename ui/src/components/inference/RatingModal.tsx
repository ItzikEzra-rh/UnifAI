import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Select, MenuItem, Box } from '@mui/material';
import StarIcon from '@mui/icons-material/Star';

// Define rating options interface
interface RatingOption {
  value: number;
  label: string;
}

const ratingOptions: RatingOption[] = [
  { value: 1, label: "The answer was incorrect or irrelevant to the code project."},
  { value: 2, label: "The answer was partially correct but lacked depth or missed key details."},
  { value: 3, label: "The answer was generally useful but had some inaccuracies or was too brief."},
  { value: 4, label: "The answer was accurate and helpful but could have included more detailed insights."},
  { value: 5, label: "The answer was complete, highly accurate, and provided expert-level insight into the code project."}
];

interface RatingModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (rating: number, ratingText: string) => void;
  initialRating?: number;
  initialRatingText?: string;
}

const RatingModal: React.FC<RatingModalProps> = ({open, onClose, onSave, initialRating = 0, initialRatingText = ''}) => {
  const [selectedRating, setSelectedRating] = React.useState<number>(initialRating);
  const [ratingText, setRatingText] = React.useState<string>(initialRatingText);

  React.useEffect(() => {
    setSelectedRating(initialRating);
    setRatingText(initialRatingText);
  }, [initialRating, initialRatingText]);

  const handleSave = () => {
    onSave(selectedRating, ratingText);
    onClose();
  };

  const renderStars = (count: number) => {
    return [...Array(count)].map((_, index) => (
      <StarIcon 
        key={index} 
        sx={{ 
          color: '#FFD700',  // Using golden yellow color
          fontSize: '20px',  // Maintaining consistent size
          marginRight: '2px' // Small gap between stars
        }} 
      />
    ));
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      PaperProps={{style: { width: '50%', margin: '0 auto' }}}
    >
      <DialogTitle>Rate Response</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Select
            value={selectedRating}
            onChange={(e) => setSelectedRating(Number(e.target.value))}
            fullWidth
            variant="standard"
            sx={{ marginTop: 2 }}
          >
            <MenuItem value={0} disabled>Select Rating</MenuItem>
            {ratingOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1}}>
                  <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 'fit-content'}}> {renderStars(option.value)} </Box>
                  <Box sx={{ flexGrow: 1, marginLeft: 1, whiteSpace: 'normal' }}> {option.label} </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>

          <TextField
            autoFocus
            margin="dense"
            label="Rating Feedback"
            type="text"
            fullWidth
            multiline
            rows={1}
            variant="standard"
            value={ratingText}
            onChange={(e) => setRatingText(e.target.value)}
            placeholder="Please provide feedback about your rating..."
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{color: "#8d8c8c"}}>Cancel</Button>
        <Button onClick={handleSave} sx={{color: "blue"}} disabled={selectedRating === 0}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RatingModal;